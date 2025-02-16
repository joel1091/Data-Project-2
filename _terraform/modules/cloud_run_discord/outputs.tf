output "service_url" {
  value = google_cloud_run_service.discord_notifier.status[0].url
}

output "service_name" {
  value = google_cloud_run_service.discord_notifier.name
}

output "latest_revision_name" {
  value = google_cloud_run_service.discord_notifier.status[0].latest_revision_name
}