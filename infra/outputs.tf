output "s3_lakehouse_bucket_arn" {
  description = "ARN of the S3 Parquet Lakehouse bucket"
  value       = aws_s3_bucket.lakehouse.arn
}

output "s3_lakehouse_bucket_name" {
  description = "Name of the S3 Parquet Lakehouse bucket"
  value       = aws_s3_bucket.lakehouse.bucket
}

output "apprunner_service_url" {
  description = "Public HTTPS endpoint for OrchardIQ App Runner service"
  value       = aws_apprunner_service.backend.service_url
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for service logs"
  value       = aws_cloudwatch_log_group.orchardiq.name
}
