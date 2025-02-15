variable "account_id" {
  description = "ID de la cuenta de servicio (sin dominio)"
  type        = string
}

variable "display_name" {
  description = "Nombre para mostrar de la cuenta de servicio"
  type        = string
}

variable "project_id" {
  description = "ID del proyecto en GCP"
  type        = string
}

variable "roles" {
  description = "Lista de roles a asignar a la cuenta de servicio"
  type        = list(string)
}
