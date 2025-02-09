resource "google_cloud_run_v2_job" "job" {
  name     = var.job_name
  location = var.region

  deletion_protection = false

  template {
    task_count = 1
    template {
      containers {
        image = var.image

        env {
          name  = "GENERATOR_TYPE"
          value = var.generator_type
        }
      }
      service_account = var.service_account_email
    }
  }
}
