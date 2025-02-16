resource "google_cloud_run_v2_service" "streamlit_app" {
  name     = var.service_name
  location = var.region

  template {
    containers {
      image = var.image_name_service 

      ports {
        container_port = 8501
      }
    }
  }
}
