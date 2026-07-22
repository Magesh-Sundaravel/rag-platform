variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the ALB."
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security groups attached to the ALB."
  type        = list(string)
}

variable "public_services" {
  description = "Public services keyed by name."
  type = map(object({
    port         = number
    health_check = string
  }))
}
