variable "build_context_dir" {
  description = "Directorio local que contiene el contexto de build (por ejemplo, app/launcher/automatic o app/launcher/manual)"
  type        = string
}

variable "output_image" {
  description = "Ruta completa (con etiqueta) de la imagen a construir y subir"
  type        = string
}

variable "project_id" {
  description = "ID del proyecto en GCP"
  type        = string
}
