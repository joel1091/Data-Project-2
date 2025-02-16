variable "location" {
  description = "La ubicación del repositorio"
  type        = string
}

variable "repository_id" {
  description = "El ID del repositorio"
  type        = string
}

variable "description" {
  description = "Descripción del repositorio"
  type        = string
  default     = ""
}

variable "format" {
  description = "Formato del repositorio (por ejemplo, DOCKER)"
  type        = string
}

variable "service_account_email" {
  description = "Email de la cuenta de servicio que usará el repositorio"
  type        = string
}

