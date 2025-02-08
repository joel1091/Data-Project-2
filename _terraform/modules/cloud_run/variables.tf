variable "job_name" {
  description = "Nombre del Cloud Run Job"
  type        = string
}

variable "image" {
  description = "Imagen del contenedor a ejecutar"
  type        = string
}

variable "region" {
  description = "Región de despliegue en Cloud Run"
  type        = string
}

variable "generator_type" {
  description = "Tipo de generador: 'automatic' o 'manual'"
  type        = string
}

variable "service_account_email" {
  description = "Email de la cuenta de servicio a asignar al Cloud Run Job"
  type        = string
}
