variable "aws_region" {
  type        = string
  description = "AWS deployment region"
  default     = "us-west-2"
}

variable "environment" {
  type        = string
  description = "Target deployment environment (development, staging, production)"
  default     = "production"
}

variable "ecr_repository_url" {
  type        = string
  description = "ECR repository URI for backend Docker image"
  default     = "123456789012.dkr.ecr.us-west-2.amazonaws.com/orchardiq-backend"
}

variable "backend_cpu" {
  type        = string
  description = "App Runner CPU allocation"
  default     = "1024"
}

variable "backend_memory" {
  type        = string
  description = "App Runner Memory allocation"
  default     = "2048"
}
