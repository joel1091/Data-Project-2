# modules/cloud_run_discord/main.tf
resource "google_cloud_run_service" "discord_notifier" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = var.image_name

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        dynamic "env" {
          for_each = var.environment_variables
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = tostring(var.max_instances)
        "autoscaling.knative.dev/minScale"      = tostring(var.min_instances)
        "run.googleapis.com/client-name"         = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.run_api
  ]
}

resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# IAM para permitir invocación desde Pub/Sub
resource "google_cloud_run_service_iam_member" "pubsub_invoker" {
  service  = google_cloud_run_service.discord_notifier.name
  location = google_cloud_run_service.discord_notifier.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_email}"
}

# CloudBuild Trigger para el despliegue automático
resource "google_cloudbuild_trigger" "discord_deploy" {
  count = var.create_trigger ? 1 : 0
  
  name        = "${var.service_name}-deploy"
  description = "Build and deploy Discord notifier to Cloud Run"

  trigger_template {
    branch_name = var.trigger_branch
    repo_name   = var.repo_name
  }

  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t",
        var.image_name,
        "./Cloud Run Function Discord"
      ]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = ["push", var.image_name]
    }

    step {
      name = "gcr.io/google.com/cloudsdktool/cloud-sdk"
      args = [
        "gcloud",
        "run",
        "deploy",
        var.service_name,
        "--image",
        var.image_name,
        "--region",
        var.region,
        "--platform",
        "managed"
      ]
    }
  }
}
