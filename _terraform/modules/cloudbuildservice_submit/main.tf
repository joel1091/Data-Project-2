# Recurso para construir y subir la imagen Docker
resource "null_resource" "build_and_push_streamlit" {
  triggers = {
    file_content_md5 = md5(file("${path.root}/../Streamlit/Dockerfile"))
    app_content_md5  = md5(file("${path.root}/../Streamlit/app.py"))
  }

  provisioner "local-exec" {
    working_dir = "${path.root}/../Streamlit"
    command     = <<-EOT
      docker build -t streamlit ${var.build_context_dir_service} && docker tag streamlit europe-west1-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository}/streamlit:${var.tag} && docker push europe-west1-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository}/streamlit:${var.tag}

      if [ $? -ne 0 ]; then
        echo "Error al subir la imagen Docker"
        exit 1
      fi
    EOT
  }
}

# Recurso para invocar el servicio de Cloud Run después de subir la imagen
resource "null_resource" "invoke_cloud_run_service" {
  depends_on = [null_resource.build_and_push_streamlit]  # Esto asegura que el servicio no se invoque hasta que la imagen esté subida

  provisioner "local-exec" {
    command = <<-EOT
      SERVICE_URL=$(gcloud run services describe ${var.service_name} --region ${var.region} --project ${var.project_id} --format "value(status.url)")
      
      # Realizar una invocación HTTP al servicio de Cloud Run usando curl
      curl -X GET $SERVICE_URL
    EOT
  }
}
