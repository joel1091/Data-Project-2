resource "null_resource" "build_and_push_docker" {


  provisioner "local-exec" {
  command = <<-EOT
    docker build --platform linux/amd64 -t launcher_automatic ${var.build_context_dir} && docker tag launcher_automatic europe-west1-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository}/launcher-automatic:${var.tag} && docker push europe-west1-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository}/launcher-automatic:${var.tag}

    if [ $? -ne 0 ]; then
      echo "Error al subir la imagen Docker"
      exit 1
    fi
  EOT
}

}

