resource "google_storage_bucket" "terraform_state" {
  name          = "terraform-bucket-dataproject-2425-abc"  
  location      = var.region
  force_destroy = true
}
