resource "google_cloud_run_v2_job" "job" {
  name                = var.job_name
  location            = var.region
  deletion_protection = false

  template {
    task_count = 1
    template {
      containers {
        image = var.image_name

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
      }
        service_account = var.service_account_email
    }
  }
    # Ejecuta el job después de que se haya creado
  provisioner "local-exec" {
    command = <<-EOT
      gcloud run jobs execute ${var.job_name} --region=${var.region} --project=${var.project_id}
    EOT

    # Solo ejecutarlo después de que el recurso se haya creado
  }
}