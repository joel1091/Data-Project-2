variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "steam-circlet-447114-h5"
}

variable "region" {
  description = "The region to deploy the Cloud Run service"
  type        = string
  default     = "europe-west1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "app"
}