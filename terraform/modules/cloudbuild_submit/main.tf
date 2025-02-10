resource "null_resource" "build_image" {
  provisioner "local-exec" {
    command = "gcloud auth configure-docker europe-west1-docker.pkg.dev && gcloud builds submit --tag ${var.output_image} ${var.build_context_dir}"
  }
}
