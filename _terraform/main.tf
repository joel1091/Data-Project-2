module "artifact_registry" {
  source         = "./modules/artifact_registry"
  repository_id  = "data-project2"
  location       = var.region
  format         = "DOCKER"
  description    = "Repositorio para imágenes Docker de Data Project 2"
}

resource "google_storage_bucket" "build_bucket" {
  name          = var.build_bucket
  location      = var.region
  force_destroy = true
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

module "sa_cloud_run" {
  source       = "./modules/service_accounts"
  account_id   = "cloud-run-sa"
  display_name = "Service Account for Cloud Run Job"
  project_id   = var.project_id
  roles        = [
    "roles/pubsub.publisher"
  ]
}

# module "sa_dataflow" {
#   source       = "./modules/service_accounts"
#   account_id   = "dataflow-sa"
#   display_name = "Service Account for Dataflow Job"
#   project_id   = var.project_id
#   roles        = [
#     "roles/pubsub.subscriber",
#     "roles/storage.objectViewer",
#     "roles/datastore.user"
#   ]
# }

module "cloud_run_automatic" {
  source                = "./modules/cloud_run"
  job_name              = "generadores-job-automatic"
  image                 = "europe-west1-docker.pkg.dev/${var.project_id}/${module.artifact_registry.repository_id}/launcher-automatic:v1"
  region                = var.region
  project_id            = var.project_id
  generator_type        = "automatic"
  service_account_email = module.sa_cloud_run.email

  depends_on = [ module.artifact_registry, module.cloudbuild_launcher_automatic ]
}

module "cloud_run_manual" {
  source                = "./modules/cloud_run"
  job_name              = "generadores-job-manual"
  image                 = "europe-west1-docker.pkg.dev/${var.project_id}/${module.artifact_registry.repository_id}/launcher-manual:v1"
  region                = var.region
  project_id            = var.project_id
  generator_type        = "manual"
  service_account_email = module.sa_cloud_run.email

  depends_on = [ module.artifact_registry, module.cloudbuild_launcher_manual ]
}


# module "dataflow_job" {
#   source                = "./modules/dataflow"
#   job_name              = "dana-help-dataflow-job"
#   project_id            = var.project_id
#   region                = var.region
#   template_gcs_path     = var.dataflow_template_gcs_path
#   parameters = {
#     ayudantes_subscription   = "projects/${var.project_id}/subscriptions/${module.pubsub_ayudantes.subscription_id}"
#     necesitados_subscription = "projects/${var.project_id}/subscriptions/${module.pubsub_necesitados.subscription_id}"
#   }
#   service_account_email = module.sa_dataflow.email
# }

module "cloudbuild_launcher_automatic" {
  source            = "./modules/cloudbuild_submit"
  build_context_dir = "../app/launcher/automatic"
  output_image      = "europe-west1-docker.pkg.dev/${var.project_id}/${module.artifact_registry.repository_id}/launcher-automatic:v1"
  project_id        = var.project_id
}

module "cloudbuild_launcher_manual" {
  source            = "./modules/cloudbuild_submit"
  build_context_dir = "../app/launcher/manual"
  output_image      = "europe-west1-docker.pkg.dev/${var.project_id}/${module.artifact_registry.repository_id}/launcher-manual:v1"
  project_id        = var.project_id
}
