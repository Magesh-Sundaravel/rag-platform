variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "service_name" {
  description = "Application service name."
  type        = string
}

variable "cluster_arn" {
  description = "ECS cluster ARN."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for tasks."
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security groups attached to tasks."
  type        = list(string)
}

variable "cloudmap_namespace_id" {
  description = "Cloud Map namespace ID."
  type        = string
}

variable "execution_role_arn" {
  description = "Task execution role ARN."
  type        = string
}

variable "task_role_arn" {
  description = "Runtime task role ARN."
  type        = string
}

variable "desired_count" {
  description = "Desired service count."
  type        = number
}

variable "cpu" {
  description = "Task CPU units."
  type        = number
}

variable "memory" {
  description = "Task memory in MiB."
  type        = number
}

variable "container_port" {
  description = "Container port."
  type        = number
}

variable "image_uri" {
  description = "Full image URI including tag."
  type        = string
}

variable "environment" {
  description = "Plain environment variables."
  type        = map(string)
}

variable "secrets" {
  description = "Secret env vars using valueFrom references."
  type        = map(string)
}

variable "assign_public_ip" {
  description = "Whether Fargate tasks receive public IPs."
  type        = bool
}

variable "enable_service_discovery" {
  description = "Whether to register the service in Cloud Map."
  type        = bool
}

variable "target_group_arn" {
  description = "Optional ALB target group ARN."
  type        = string
  default     = null
}

variable "aws_region" {
  description = "AWS region for CloudWatch logging."
  type        = string
  default     = "eu-west-1"
}
