resource "google_cloud_run_v2_job" "job" {
  name     = var.job_name
  location = var.region

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
