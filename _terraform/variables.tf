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

variable "repository_id" {
  description = "El ID del repositorio"
  type        = string  
}

variable "image_name" {
  description = "Nombre de la imagen Docker"
  type        = string
}

variable "tag" {
  description = "Etiqueta para la imagen Docker"
  type        = string
}

variable "build_context_dir" {
  description = "Directorio de contexto para la construcción de la imagen Docker."
  type        = string
}

variable "job_name" {
  description = "Nombre del trabajo de Cloud Build"
  type        = string
}

