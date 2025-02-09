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
