variable "image_name_grafana" {
  description = "Nombre del servicio de Cloud Run para Grafana"
  type        = string
}

variable "region" {
  description = "Región de GCP donde se desplegará el servicio"
  type        = string

}

variable "roles" {
  description = "Lista de roles a asignar a la cuenta de servicio de Grafana"
  type        = list(string)
}