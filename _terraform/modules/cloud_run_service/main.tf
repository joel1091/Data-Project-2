resource "google_cloud_run_v2_service" "streamlit_app" {
  name     = var.service_name
  location = var.region
  deletion_protection = false

  template {
    containers {
      image = var.image_name_service 

      env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

      ports {
        container_port = 8501
      }
    }
  }
}

