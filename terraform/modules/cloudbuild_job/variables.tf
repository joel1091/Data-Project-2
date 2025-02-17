variable "project_id" {
  description = "ID del proyecto en GCP"
  type        = string
}

variable "region" {
  description = "Región de despliegue en GCP"
  type        = string
}

variable "job_name" {
  description = "Nombre del trabajo de Cloud Build"
  type        = string
}

variable "image_name" {
  description = "Nombre de la imagen Docker"
  type        = string
}

variable "service_account_email" {
  description = "Correo electrónico de la cuenta de servicio"
  type        = string
}