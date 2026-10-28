terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "OrchardIQ"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# ==========================================================
# 1. S3 Parquet Lakehouse Storage
# ==========================================================
resource "aws_s3_bucket" "lakehouse" {
  bucket        = "orchardiq-lakehouse-${var.environment}-${var.aws_region}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "lakehouse_versioning" {
  bucket = aws_s3_bucket.lakehouse.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lakehouse_encryption" {
  bucket = aws_s3_bucket.lakehouse.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "lakehouse_lifecycle" {
  bucket = aws_s3_bucket.lakehouse.id

  rule {
    id     = "raw_partition_tiering"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

# ==========================================================
# 2. AWS App Runner Service (FastAPI Container)
# ==========================================================
resource "aws_apprunner_service" "backend" {
  service_name = "orchardiq-backend-${var.environment}"

  source_configuration {
    auto_deployments_enabled = true

    image_repository {
      image_identifier      = "${var.ecr_repository_url}:latest"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          ENVIRONMENT         = var.environment
          DEMO_MODE           = "true"
          MOCK_LLM_MODE       = "true"
          S3_BUCKET           = aws_s3_bucket.lakehouse.bucket
          S3_REGION           = var.aws_region
          DUCKDB_MEMORY_LIMIT = "2GB"
        }
      }
    }
  }

  instance_configuration {
    cpu    = var.backend_cpu
    memory = var.backend_memory
  }
}

# ==========================================================
# 3. CloudWatch Logging & Observability Alarms
# ==========================================================
resource "aws_cloudwatch_log_group" "orchardiq" {
  name              = "/aws/apprunner/orchardiq-${var.environment}"
  retention_in_days = 30
}

resource "aws_cloudwatch_metric_alarm" "latency_alarm" {
  alarm_name          = "orchardiq-p95-latency-exceeded-${var.environment}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "Latency"
  namespace           = "AWS/AppRunner"
  period              = 60
  statistic           = "p95"
  threshold           = 2000 # 2000 ms = 2.0s
  alarm_description   = "Triggers when OrchardIQ p95 latency exceeds 2.0 seconds."
  actions_enabled     = true
}

resource "aws_cloudwatch_metric_alarm" "governance_rejection_alarm" {
  alarm_name          = "orchardiq-guardrail-rejection-spike-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "GuardrailRejections"
  namespace           = "OrchardIQ/Governance"
  period              = 300
  statistic           = "Sum"
  threshold           = 25
  alarm_description   = "Triggers when anomalous volume of hostile or unauthorized queries is blocked."
  actions_enabled     = true
}
