resource "google_service_account" "prueba" {
  account_id   = var.account_id
  display_name = var.display_name
  project      = var.project_id
}

resource "google_project_iam_member" "prueba" {
  count   = length(var.roles)
  project = var.project_id
  role    = var.roles[count.index]
  member  = "serviceAccount:${google_service_account.prueba.email}"
}