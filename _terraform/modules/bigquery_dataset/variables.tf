variable "project" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "location" {
  description = "Región para el dataset de BigQuery"
  type        = string
}

variable "dataset_id" {
  description = "ID del dataset en BigQuery"
  type        = string
}
