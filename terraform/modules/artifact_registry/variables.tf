variable "repository_id" {
  description = "ID del repositorio de Artifact Registry"
  type        = string
}

variable "location" {
  description = "Ubicación para el repositorio (ej. europe-west1)"
  type        = string
}

variable "format" {
  description = "Formato del repositorio (ej. DOCKER)"
  type        = string
}

variable "description" {
  description = "Descripción del repositorio"
  type        = string
  default     = ""
}

variable "service_account_email" {
  description = "Correo electrónico de la cuenta de servicio que tendrá permisos para subir imágenes"
  type        = string
}