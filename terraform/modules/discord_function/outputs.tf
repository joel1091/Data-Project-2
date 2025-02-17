output "function_name" {
  description = "Nombre de la Cloud Function desplegada"
  value       = google_cloudfunctions2_function.notify_discord_v2.name
}
