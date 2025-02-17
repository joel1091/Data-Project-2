variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "region" {
  description = "Región donde se ejecuta el servicio de Cloud Run"
  type        = string
}

variable "service_name" {
  description = "Nombre del Cloud Run Service"
  type = string
}

variable "image_name_service" {
  description = "Nombre de la imagen Docker"
  type        = string
}

variable "service_account_email" {
  description = "Email de la cuenta de servicio que usará el servicio de Cloud Run"
  type        = string
}

