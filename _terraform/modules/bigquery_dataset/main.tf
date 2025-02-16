resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.dataset_id
  project    = var.project
  location   = var.location
}