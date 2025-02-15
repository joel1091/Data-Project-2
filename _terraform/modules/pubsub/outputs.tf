output "topic_id" {
  value = google_pubsub_topic.prueba.name
}

output "subscription_id" {
  value = google_pubsub_subscription.prueba.name
}
