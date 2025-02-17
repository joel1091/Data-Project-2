resource "google_cloud_run_service" "grafana" {
  name     = var.image_name_grafana
  location = var.region

  template {
    spec {
      containers {
        image = "grafana/grafana:latest"
        ports {
          container_port = 3000
        }
        env {
          name  = "GF_SECURITY_ADMIN_USER"
          value = "admin"
        }
        env {
          name  = "GF_SECURITY_ADMIN_PASSWORD"
          value = "dataproject2"
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}
