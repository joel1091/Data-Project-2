resource "google_storage_bucket" "terraform_state" {
  name          = "dataproject2-alobce-terraform-state"
  location      = var.region #europe-west1
  force_destroy = true
}