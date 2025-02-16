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
  description = "El ID del repositorio en Artifact Registry"
  type        = string
}

variable "image_name" {
  description = "Nombre de la imagen Docker"
  type        = string
}

variable "image_name_service" {
  description = "Nombre de la imagen de Docker"
  type = string
}

variable "tag" {
  description = "Etiqueta para la imagen Docker"
  type        = string
}

variable "build_context_dir" {
  description = "Directorio de contexto para la construcción de la imagen Docker."
  type        = string
}

variable "build_context_dir_service" {
  description = "Directorio de contexto para la construcción de la imagen Docker Service."
  type        = string
}

variable "job_name" {
  description = "Nombre del trabajo de Cloud Build"
  type        = string
}

variable "service_name" {
  description = "Nombre del Cloud Run Service"
  type = string
}

variable "grafana_service_name"{
  description = "Nombre de Grafana Service"
  type = string
}

variable "trigger_name" {
  description = "Nombre del trigger de Cloud Build"
  type        = string
}

variable "trigger_description" {
  description = "Descripción del trigger"
  type        = string
  default     = "Trigger para Dataflow Flex Template"
}

variable "github_owner" {
  description = "Owner del repositorio GitHub"
  type        = string
}

variable "github_repo_name" {
  description = "Nombre del repositorio GitHub"
  type        = string
}

variable "github_branch" {
  description = "Rama del repositorio GitHub que dispara el trigger"
  type        = string
  default     = "main"
}

variable "build_filename" {
  description = "Nombre del archivo de Cloud Build en el repositorio"
  type        = string
  default     = "build.yml"
}

variable "dataflow_base_bucket" {
  description = "Nombre del bucket donde se almacenará el template"
  type        = string
}

variable "dataflow_job_name" {
  description = "Nombre del trabajo de Dataflow"
  type        = string
}

variable "dataflow_template_name" {
  description = "Nombre del template de Dataflow"
  type        = string
}

variable "region_id" {
  description = "Región de despliegue de GCP"
  type        = string
}


variable "artifact_registry_image_name" {
  description = "Nombre de la imagen en Artifact Registry"
  type        = string
}

variable "dataflow_python_file_path" {
  description = "Ruta al archivo Python para Dataflow"
  type        = string
}

variable "dataflow_requirements_file_path" {
  description = "Ruta al archivo requirements.txt para Dataflow"
  type        = string
}

variable "volunteer_topic_name" {
  description = "Nombre del tópico para voluntarios"
  type        = string
}

variable "volunteer_pubsub_subscription_name" {
  description = "Nombre de la suscripción de Pub/Sub para voluntarios"
  type        = string
}

variable "help_topic_name" {
  description = "Nombre del tópico de ayuda"
  type        = string
}

variable "help_pubsub_subscription_name" {
  description = "Nombre de la suscripción de Pub/Sub para ayuda"
  type        = string
}

variable "bigquery_dataset_name" {
  description = "Nombre del dataset de BigQuery"
  type        = string
}

variable "artifact_registry_repository" {
  description = "Nombre del repositorio en Artifact Registry"
  type        = string
}
