variable "project_id" {
  description = "ID del proyecto en GCP"
  type        = string
}

variable "location" {
  description = "Región en la que se encuentra el servicio de Cloud Run"
  type        = string
}

variable "service" {
  description = "Nombre del servicio de Cloud Run"
  type        = string
}

variable "role" {
  description = "Rol a asignar"
  type        = string
  default     = "roles/run.invoker"
}

variable "member" {
  description = "Miembro al que se le asignará el rol (por ejemplo, allUsers)"
  type        = string
  default     = "allUsers"
}
