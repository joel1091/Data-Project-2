########## TENEMOS UN BUCKET NO?
resource "google_storage_bucket" "function_bucket" {
  name     = "<NAME BUCKET>"
  location = "europe-west1"
}

# Subir el archivo .zip al bucket de GCS
resource "google_storage_bucket_object" "discord_function_zip" {
  name   = "discord-function.zip"
  bucket = google_storage_bucket.function_bucket.name  # Nombre del bucket
  source = "./discord-function.zip"       # Ruta al archivo .zip en tu máquina local
  content_type = "application/zip"
}

# Crear la Google Cloud Function
resource "google_cloudfunctions_function" "discord_function" {
  name        = "discord-function"
  description = "Function for discord"
  runtime     = "python39"
  region      = "europe-west1"
  entry_point = "notify_discord"

  source_archive_bucket = google_storage_bucket.function_bucket.name        
  source_archive_object = google_storage_bucket_object.discord_function_zip.name  

  event_trigger {
    event_type = "google.pubsub.topic.publish" 
    resource   = "projects/<project_id>/topics/matched-events" ######## variable
  }

  environment_variables = {
    MY_ENV_VAR = "value"
  }
}
