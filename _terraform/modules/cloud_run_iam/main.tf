resource "google_cloud_run_v2_service_iam_member" "this" {
  project  = var.project_id
  location = var.location
  name  = var.service

  role   = var.role
  member = var.member
}