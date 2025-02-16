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
  depends_on = [null_resource.build_and_push_streamlit]  # Asegura que la imagen se haya subido

  provisioner "local-exec" {
    interpreter = ["cmd", "/C"]
    command = <<-EOT
      for /f "tokens=*" %i in ('gcloud run services describe ${var.service_name} --region ${var.region} --project ${var.project_id} --format "value(status.url)"') do (
        set URL=%i
      )
      echo Invoking service at: %URL%
      curl -X GET %URL%
    EOT
  }
}


