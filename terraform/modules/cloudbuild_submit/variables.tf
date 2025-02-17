variable "region" {
  description = "La región en la que se encuentran los recursos."
  type        = string
}

variable "project_id" {
  description = "ID del proyecto de Google Cloud."
  type        = string
}

variable "image_name" {
  description = "Nombre de la imagen Docker."
  type        = string
}

variable "tag" {
  description = "Etiqueta de la imagen Docker."
  type        = string
}

variable "build_context_dir" {
  description = "Directorio de contexto para la construcción de la imagen Docker."
  type        = string
}

variable "artifact_registry_repository" {
  description = "El repositorio de Artifact Registry donde se almacenará la imagen Docker."
  type        = string
}

