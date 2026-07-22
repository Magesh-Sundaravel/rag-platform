variable "aws_region" {
  description = "AWS region for the deployment."
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Short project identifier used in AWS resource names."
  type        = string
  default     = "rag-platform"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the application VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Exactly two public subnet CIDRs for the ALB and NAT gateway."
  type        = list(string)
  default     = ["10.40.0.0/24", "10.40.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "Exactly two private subnet CIDRs for ECS tasks and RDS."
  type        = list(string)
  default     = ["10.40.10.0/24", "10.40.11.0/24"]
}

variable "db_name" {
  description = "RDS database name."
  type        = string
  default     = "rag"
}

variable "db_username" {
  description = "Master username for the RDS instance."
  type        = string
  default     = "rag"
}

variable "db_password" {
  description = "Master password for the RDS instance."
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Allocated RDS storage in GiB."
  type        = number
  default     = 30
}

variable "service_image_tag" {
  description = "Default image tag applied to all services when no per-service override is supplied."
  type        = string
  default     = "latest"
}

variable "service_image_tags" {
  description = "Optional per-service image tag overrides."
  type        = map(string)
  default     = {}
}

variable "service_cpu" {
  description = "CPU units per ECS task definition."
  type        = map(number)
  default = {
    ingestion  = 512
    processing = 512
    retrieval  = 512
    generation = 512
  }
}

variable "service_memory" {
  description = "Memory (MiB) per ECS task definition."
  type        = map(number)
  default = {
    ingestion  = 1024
    processing = 1024
    retrieval  = 1024
    generation = 1024
  }
}

variable "service_desired_count" {
  description = "Desired ECS task count per service."
  type        = map(number)
  default = {
    ingestion  = 1
    processing = 1
    retrieval  = 1
    generation = 1
  }
}

variable "service_environment" {
  description = "Plaintext environment variables for each service."
  type        = map(map(string))
  default     = {}
}

variable "service_secrets" {
  description = "Secret ARNs or SSM parameter ARNs for each service, keyed by environment variable name."
  type        = map(map(string))
  default     = {}
}

variable "otel_exporter_endpoint" {
  description = "Optional OTLP/HTTP collector endpoint."
  type        = string
  default     = null
}
