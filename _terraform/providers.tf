

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

terraform {
  backend "gcs" {
    bucket = "dataproject2-alobce-terraform-state"  
    prefix = "terraform/state"        
  }
}


terraform {
  required_version = ">= 1.3.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.91.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 4.91.0"
    }
  }


}
