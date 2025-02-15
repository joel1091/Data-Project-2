output "service_url" {
  value = google_cloud_run_service.streamlit_app.status[0].url
}

output "service_name" {
  value = google_cloud_run_service.streamlit_app.name
}

output "service_region" {
  value = google_cloud_run_service.streamlit_app.location
}