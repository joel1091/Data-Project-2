output "build_id" {
  description = "ID del build ejecutado (valor del null_resource)"
  value       = null_resource.build_image.id
}
