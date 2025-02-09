output "repository_id" {
  description = "ID del repositorio de Artifact Registry"
  value       = google_artifact_registry_repository.repo.repository_id
}
