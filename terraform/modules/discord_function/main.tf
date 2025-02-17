resource "google_cloudfunctions2_function" "notify_discord_v2" {
  name     = "notify-discord-v2"
  location = var.region
  project  = var.project_id

build_config {
  runtime           = "python310"  # O la versión de Python que necesites
  entry_point       = var.entry_point
  docker_repository = "projects/${var.project_id}/locations/${var.region}/repositories/${var.repository_id}"
  
  source {
    storage_source {
      bucket = google_storage_bucket.functions_source.name
      object = google_storage_bucket_object.empty_zip.name
    }
  }
}

  service_config {
    ingress_settings   = "ALLOW_ALL"
    max_instance_count = 1
  }

  event_trigger {
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    trigger_region = var.region
    pubsub_topic   = var.pubsub_topic
  }
}


resource "google_storage_bucket" "functions_source" {
  name     = "${var.project_id}-functions-source"
  location = var.region
}

resource "google_storage_bucket_object" "empty_zip" {
  name   = "empty.zip"
  bucket = google_storage_bucket.functions_source.name
  source = "../discord/empty.zip"  # Ruta al archivo ZIP en tu máquina local
}