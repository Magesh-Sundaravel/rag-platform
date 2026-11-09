output "alb_dns_name" {
  description = "Public ALB DNS name."
  value       = module.alb.dns_name
}

output "cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.main.name
}

output "cloudmap_namespace" {
  description = "Private DNS namespace for service-to-service traffic."
  value       = aws_service_discovery_private_dns_namespace.services.name
}

output "database_endpoint" {
  description = "RDS endpoint hostname."
  value       = module.rds.endpoint
}

output "ecr_repository_urls" {
  description = "Per-service ECR repository URLs."
  value       = module.ecr.repository_urls
}

output "service_names" {
  description = "ECS service names keyed by application service."
  value = {
    for name, module_ref in module.ecs_service :
    name => module_ref.service_name
  }
}

output "processing_queue_url" {
  description = "SQS queue URL for ingestion → processing hand-off."
  value       = aws_sqs_queue.processing.url
}

output "processing_dlq_url" {
  description = "Dead-letter queue URL for documents that failed processing."
  value       = aws_sqs_queue.processing_dlq.url
}
