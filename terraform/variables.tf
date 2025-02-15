variable "project_id" {
  description = "ID del proyecto en GCP"
  type        = string
}

variable "region" {
  description = "Región de despliegue en GCP"
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "Zona de despliegue en GCP (por ejemplo, europe-west1-b)"
  type        = string
}

variable "build_bucket" {
  description = "Nombre del bucket de Cloud Storage para subir el contexto de build"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "app"
}

variable "subnetwork" {
  description = "La subred a la que se desplegará"
  type        = string
}

variable "service_account_email" {
  description = "El email de la cuenta de servicio a utilizar"
  type        = string
}

# variable "dataflow_template_gcs_path" {
#   description = "Ruta al Dataflow Flex Template en GCS"
#   type        = string
# }
