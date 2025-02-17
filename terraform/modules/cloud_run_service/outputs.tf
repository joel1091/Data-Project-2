output "name" {
  value = google_cloud_run_v2_service.streamlit_app.name
}

output "location" {
  value = google_cloud_run_v2_service.streamlit_app.location
}

output "streamlit_app_url" {
  value       = google_cloud_run_v2_service.streamlit_app.uri
  description = "La URL pública del servicio de Cloud Run para la aplicación Streamlit."
}


