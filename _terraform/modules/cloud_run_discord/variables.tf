variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
}

variable "image_name" {
  description = "Container image name"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for Pub/Sub invoker"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for the service"
  type        = map(string)
  default     = {}
}

variable "cpu" {
  description = "CPU allocation"
  type        = string
  default     = "1000m"
}

variable "memory" {
  description = "Memory allocation"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 100
}

variable "create_trigger" {
  description = "Whether to create a Cloud Build trigger"
  type        = bool
  default     = true
}

variable "trigger_branch" {
  description = "Branch to trigger build from"
  type        = string
  default     = "main"
}

variable "repo_name" {
  description = "Repository name for Cloud Build trigger"
  type        = string
  default     = ""
}