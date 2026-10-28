# OrchardIQ AWS Infrastructure Plan (`terraform plan`)

This document records the exact planned infrastructure provisioning executed for OrchardIQ on AWS.

```text
Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_apprunner_service.backend will be created
  + resource "aws_apprunner_service" "backend" {
      + arn                   = (known after apply)
      + auto_scaling_configuration_arn = (known after apply)
      + id                    = (known after apply)
      + service_id            = (known after apply)
      + service_name          = "orchardiq-backend-production"
      + service_url           = (known after apply)
      + status                = (known after apply)

      + instance_configuration {
          + cpu    = "1024"
          + memory = "2048"
        }

      + source_configuration {
          + auto_deployments_enabled = true

          + image_repository {
              + image_identifier      = "123456789012.dkr.ecr.us-west-2.amazonaws.com/orchardiq-backend:latest"
              + image_repository_type = "ECR"

              + image_configuration {
                  + port                          = "8000"
                  + runtime_environment_variables = {
                      + "DEMO_MODE"           = "true"
                      + "DUCKDB_MEMORY_LIMIT" = "2GB"
                      + "ENVIRONMENT"         = "production"
                      + "MOCK_LLM_MODE"       = "true"
                      + "S3_BUCKET"           = "orchardiq-lakehouse-production-us-west-2"
                      + "S3_REGION"           = "us-west-2"
                    }
                }
            }
        }
    }

  # aws_cloudwatch_log_group.orchardiq will be created
  + resource "aws_cloudwatch_log_group" "orchardiq" {
      + arn               = (known after apply)
      + id                = (known after apply)
      + name              = "/aws/apprunner/orchardiq-production"
      + retention_in_days = 30
      + tags_all          = {
          + "Environment" = "production"
          + "ManagedBy"   = "Terraform"
          + "Project"     = "OrchardIQ"
        }
    }

  # aws_cloudwatch_metric_alarm.governance_rejection_alarm will be created
  + resource "aws_cloudwatch_metric_alarm" "governance_rejection_alarm" {
      + actions_enabled     = true
      + alarm_description   = "Triggers when anomalous volume of hostile or unauthorized queries is blocked."
      + alarm_name          = "orchardiq-guardrail-rejection-spike-production"
      + comparison_operator = "GreaterThanThreshold"
      + evaluation_periods  = 1
      + metric_name         = "GuardrailRejections"
      + namespace           = "OrchardIQ/Governance"
      + period              = 300
      + statistic           = "Sum"
      + threshold           = 25
    }

  # aws_cloudwatch_metric_alarm.latency_alarm will be created
  + resource "aws_cloudwatch_metric_alarm" "latency_alarm" {
      + actions_enabled     = true
      + alarm_description   = "Triggers when OrchardIQ p95 latency exceeds 2.0 seconds."
      + alarm_name          = "orchardiq-p95-latency-exceeded-production"
      + comparison_operator = "GreaterThanOrEqualToThreshold"
      + evaluation_periods  = 2
      + metric_name         = "Latency"
      + namespace           = "AWS/AppRunner"
      + period              = 60
      + statistic           = "p95"
      + threshold           = 2000
    }

  # aws_s3_bucket.lakehouse will be created
  + resource "aws_s3_bucket" "lakehouse" {
      + acceleration_status         = (known after apply)
      + acl                         = (known after apply)
      + arn                         = (known after apply)
      + bucket                      = "orchardiq-lakehouse-production-us-west-2"
      + bucket_domain_name          = (known after apply)
      + force_destroy               = false
      + id                          = (known after apply)
    }

  # aws_s3_bucket_lifecycle_configuration.lakehouse_lifecycle will be created
  + resource "aws_s3_bucket_lifecycle_configuration" "lakehouse_lifecycle" {
      + bucket = (known after apply)
      + id     = (known after apply)

      + rule {
          + id     = "raw_partition_tiering"
          + status = "Enabled"

          + filter {
              + prefix = "raw/"
            }

          + transition {
              + days          = 90
              + storage_class = "GLACIER"
            }
        }
    }

  # aws_s3_bucket_server_side_encryption_configuration.lakehouse_encryption will be created
  + resource "aws_s3_bucket_server_side_encryption_configuration" "lakehouse_encryption" {
      + bucket = (known after apply)
      + id     = (known after apply)

      + rule {
          + apply_server_side_encryption_by_default {
              + sse_algorithm = "AES256"
            }
        }
    }

  # aws_s3_bucket_versioning.lakehouse_versioning will be created
  + resource "aws_s3_bucket_versioning" "lakehouse_versioning" {
      + bucket = (known after apply)
      + id     = (known after apply)

      + versioning_configuration {
          + status = "Enabled"
        }
    }

Plan: 8 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + apprunner_service_url    = (known after apply)
  + cloudwatch_log_group     = "/aws/apprunner/orchardiq-production"
  + s3_lakehouse_bucket_arn  = (known after apply)
  + s3_lakehouse_bucket_name = "orchardiq-lakehouse-production-us-west-2"
```
