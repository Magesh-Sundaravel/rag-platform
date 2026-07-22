variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "repositories" {
  description = "Repositories keyed by service name."
  type        = map(string)
}
