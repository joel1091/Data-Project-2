output "pubsub_ayudantes_topic" {
  value = module.pubsub_ayudantes.topic_id
}

output "pubsub_ayudantes_subscription" {
  value = module.pubsub_ayudantes.subscription_id
}

output "pubsub_necesitados_topic" {
  value = module.pubsub_necesitados.topic_id
}

output "pubsub_necesitados_subscription" {
  value = module.pubsub_necesitados.subscription_id
}

output "cloud_run_automatic_job" {
  value = module.cloud_run_automatic.job_name
}

output "cloud_run_manual_job" {
  value = module.cloud_run_manual.job_name
}

# output "dataflow_job_id" {
#   value = module.dataflow_job.dataflow_job_id
# }

output "sa_cloud_run_email" {
  value = module.sa_cloud_run.email
}

# output "sa_dataflow_email" {
#   value = module.sa_dataflow.email
# }

output "cloudbuild_launcher_automatic_build_id" {
  value = module.cloudbuild_launcher_automatic.build_id
}

output "cloudbuild_launcher_manual_build_id" {
  value = module.cloudbuild_launcher_manual.build_id
}