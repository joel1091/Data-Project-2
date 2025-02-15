resource "google_cloud_run_service" "streamlit_app" {
  name     = var.service_name
  location = var.region
  
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/streamlit-app"
        
        ports {
          container_port = 8501
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Make the service public
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.streamlit_app.name
  location = google_cloud_run_service.streamlit_app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Build and push the container image
resource "null_resource" "build_and_push" {
  triggers = {
    file_content_md5 = md5(file("${path.root}/../Streamlit/Dockerfile"))
    app_content_md5  = md5(file("${path.root}/../Streamlit/app.py"))
  }

  provisioner "local-exec" {
    working_dir = "${path.root}/../Streamlit"
    command     = "gcloud builds submit --tag gcr.io/${var.project_id}/streamlit-app"
  }
}