# resource "google_cloudbuild_trigger" "dataflow_trigger" {
#   name        = var.trigger_name
#   description = var.trigger_description

#   github {
#     owner = var.github_owner
#     name  = var.github_repo_name

#     push {
#       branch = var.github_branch
#     }
#   }

#   filename = var.build_filename

#   substitutions = {
#     _DATAFLOW_BASE_BUCKET               = var.dataflow_base_bucket
#     _DATAFLOW_JOB_NAME                  = var.dataflow_job_name
#     _DATAFLOW_TEMPLATE_NAME             = var.dataflow_template_name
#     _REGION_ID                          = var.region_id
#     _ARTIFACT_REGISTRY_REPOSITORY       = var.artifact_registry_repository
#     _ARTIFACT_REGISTRY_IMAGE_NAME       = var.artifact_registry_image_name
#     _DATAFLOW_PYTHON_FILE_PATH          = var.dataflow_python_file_path
#     _DATAFLOW_REQUIREMENTS_FILE_PATH    = var.dataflow_requirements_file_path
#     _VOLUNTEER_TOPIC_NAME              = var.volunteer_topic_name
#     _VOLUNTEER_PUBSUB_SUBSCRIPTION_NAME = var.volunteer_pubsub_subscription_name
#     _HELP_TOPIC_NAME                    = var.help_topic_name
#     _HELP_PUBSUB_SUBSCRIPTION_NAME      = var.help_pubsub_subscription_name
#     _BIGQUERY_DATASET_NAME_             = var.bigquery_dataset_name
#   }
# }
