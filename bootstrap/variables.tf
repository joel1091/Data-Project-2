variable  "project_id" {
  type        = string
  description = "ID del proyecto de GCP"
}

variable "region" {
  type        = string
  description = "Región de GCP"
  default     = "europe-west1"
}

variable "zone" {
  type        = string
  description = "Zona de GCP"
}