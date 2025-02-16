variable "project" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "dataset_id" {
  description = "ID del dataset donde se creará la tabla"
  type        = string
}

variable "table_id" {
  description = "ID de la tabla en BigQuery"
  type        = string
}

variable "schema_file" {
  description = "Ruta al archivo JSON que contiene el esquema"
  type        = string
}
