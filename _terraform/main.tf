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



