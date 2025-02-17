variable "project_id" {
  description = "El ID del proyecto de Google Cloud"
  type        = string
}

variable "region" {
  description = "La región donde se ejecuta el servicio de Cloud Run"
  type        = string
}

variable "service_name" {
  description = "El nombre del servicio de Cloud Run"
  type        = string
}

variable "tag" {
  description = "La etiqueta de la imagen Docker"
  type        = string
}

variable "build_context_dir_service" {
  description = "El directorio de contexto de la imagen Docker para el servicio Streamlit"
  type        = string
}


variable "artifact_registry_repository" {
  description = "El repositorio de Artifact Registry donde se almacenará la imagen Docker."
  type        = string
}