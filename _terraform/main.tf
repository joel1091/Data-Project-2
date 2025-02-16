module "sa_artifact_registry" {
  source       = "./modules/service_accounts"
  account_id   = "artifact-registry-sa"
  display_name = "Service Account for Artifact Registry"
  project_id   = var.project_id
  roles        = [
    "roles/artifactregistry.writer"
  ]  
}

module "artifact_registry" {
  source         = "./modules/artifact_registry"
  repository_id  = var.repository_id
  location       = var.region
  format         = "DOCKER"
  service_account_email = module.sa_artifact_registry.email
  description    = "Repositorio para imágenes Docker de Data Project 2"

  depends_on = [
    module.pubsub_ayudantes,
    module.pubsub_necesitados,
    module.pubsub_matched
  ]
}

module "pubsub_ayudantes" {
  source            = "./modules/pubsub"
  topic_name        = "ayudantes-events"
  subscription_name = "ayudantes-events-sub"
}

module "pubsub_necesitados" {
  source            = "./modules/pubsub"
  topic_name        = "necesitados-events"
  subscription_name = "necesitados-events-sub"
}

module "pubsub_matched" {
  source            = "./modules/pubsub"
  topic_name        = "matched-events"
  subscription_name = "matched-events-sub"
}

module "cloudbuild_launcher_automatic" {
  source                     = "./modules/cloudbuild_submit"
  region                     = var.region
  project_id                 = var.project_id
  tag                        = var.tag
  image_name                 = var.image_name
  artifact_registry_repository = module.artifact_registry.repository_id
  build_context_dir          = var.build_context_dir

  depends_on = [module.artifact_registry]
}

module "sa_cloud_run" {
  source       = "./modules/service_accounts"
  account_id   = "cloud-run-sa"
  display_name = "Service Account for Cloud Run Job"
  project_id   = var.project_id
  roles        = [
    "roles/pubsub.publisher"
  ]
}

module "cloud_run_automatic" {
  source                = "./modules/cloudbuild_job"
  job_name              = var.job_name
  image_name           = "europe-west1-docker.pkg.dev/${var.project_id}/${var.repository_id}/${var.image_name}:${var.tag}"
  region                = var.region
  project_id            = var.project_id
  service_account_email = module.sa_cloud_run.email

  depends_on = [module.artifact_registry, module.cloudbuild_launcher_automatic]
}

module "sa_cloud_run_service" {
  source       = "./modules/service_accounts"
  account_id   = "cloud-run-service-sa"
  display_name = "Service Account for Cloud Run Service"
  project_id   = var.project_id
  roles        = [
    "roles/pubsub.subscriber",  
    "roles/pubsub.publisher"    
  ]
}

module "cloud_run_iam_invoker" {
  source     = "./modules/cloud_run_iam"
  project_id = var.project_id
  location   = module.cloud_run_service.location
  service    = module.cloud_run_service.name  
  role       = "roles/run.invoker"
  member     = "allUsers"
}

module "cloudbuildservice_submit" {
  source                     = "./modules/cloudbuildservice_submit"
  region                     = var.region
  project_id                 = var.project_id
  tag                        = var.tag
  service_name               = var.service_name
  artifact_registry_repository = module.artifact_registry.repository_id
  build_context_dir_service          = var.build_context_dir_service

  depends_on = [module.artifact_registry]
}

module "cloud_run_service" {
  source                = "./modules/cloud_run_service"
  service_name             = var.service_name
  image_name_service      = "europe-west1-docker.pkg.dev/${var.project_id}/${var.repository_id}/${var.image_name_service}:${var.tag}"
  region                = var.region
  project_id            = var.project_id
  service_account_email = module.sa_cloud_run_service.email

  depends_on = [module.artifact_registry, module.cloudbuildservice_submit]
}

# Crear un único dataset (por ejemplo, "common-dataset")
module "bigquery_dataset" {
  source     = "./modules/bigquery_dataset"
  project    = var.project_id
  location   = var.region
  dataset_id = "users"
}

# Crear la tabla "ayudantes"
module "bigquery_ayudantes" {
  source      = "./modules/bigquery_table"
  project     = var.project_id
  dataset_id  = module.bigquery_dataset.dataset_id
  table_id    = "unmatched_volunteers"
  schema_file = "/schemas/volunteer.json"
}

# Crear la tabla "necesitados"
module "bigquery_necesitados" {
  source      = "./modules/bigquery_table"
  project     = var.project_id
  dataset_id  = module.bigquery_dataset.dataset_id
  table_id    = "unmatched_requests"
  schema_file = "/schemas/requests.json"
}

# Crear la tabla "matched"
module "bigquery_matched" {
  source      = "./modules/bigquery_table"
  project     = var.project_id
  dataset_id  = module.bigquery_dataset.dataset_id
  table_id    = "matched_pairs"
  schema_file = "/schemas//matched.json"
}

module "grafana" {
  source             = "./modules/cloud_run_grafana"
  image_name_grafana = var.grafana_service_name
  region             = var.region

  roles = [
    "roles/bigquery.dataviewer",
    "roles/bigquery.jobUser"
  ]
}

module "grafana_iam_invoker" {
  source     = "./modules/cloud_run_iam"
  project_id = var.project_id
  location   = module.grafana.region
  service    = module.grafana.name
  role       = "roles/run.invoker"
  member     = "allUsers"
}


#ESTO ES LO NUEVO QUE HE PUESTO

module "discord_notifier" {
  source = "./modules/cloud_run_discord"
  
  project_id            = var.project_id
  region               = var.region
  service_name         = "discord-notifier"
  image_name           = "gcr.io/${var.project_id}/discord-notifier:latest"
  service_account_email = module.service_accounts.pubsub_sa_email # o el email de tu SA
  
  environment_variables = {
    DISCORD_WEBHOOK_URL = var.discord_webhook_url
    # Otras variables de entorno necesarias
  }
  
  create_trigger = true
  repo_name      = "your-repo-name"
  trigger_branch = "main"
}

