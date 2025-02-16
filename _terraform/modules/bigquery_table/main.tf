resource "google_bigquery_table" "table" {
  dataset_id = var.dataset_id
  table_id   = var.table_id
  schema     = file(var.schema_file)
  project    = var.project
  deletion_protection=false
}
