
# ayudantes_events Pub/Sub topic and subscription
resource "google_pubsub_topic" "ayudantes_events" {
  name = "ayudantes-events"
}

resource "google_pubsub_subscription" "ayudantes_events_sub" {
  name  = "${google_pubsub_topic.ayudantes_events.name}-sub"
  topic = google_pubsub_topic.ayudantes_events.name
}

# necesitados_events Pub/Sub topic and subscription
resource "google_pubsub_topic" "necesitados_events" {
  name = "necesitados-events"
}

resource "google_pubsub_subscription" "necesitados_events_sub" {
  name  = "${google_pubsub_topic.necesitados_events.name}-sub"
  topic = google_pubsub_topic.necesitados_events.name
}

#######--------------------------------------------------------

# Ayudantes Dead Letter Topic and Subscription
resource "google_pubsub_topic" "ayudantes_events_dead_letter" {
  name = "ayudantes-events-dead-letter"
}

resource "google_pubsub_subscription" "ayudantes_events_dead_letter_sub" {
  name  = "ayudantes-events-dead-letter-sub"
  topic = google_pubsub_topic.ayudantes_events_dead_letter.name
}

# Necesitados Dead Letter Topic and Subscription
resource "google_pubsub_topic" "necesitados_events_dead_letter" {
  name = "necesitados-events-dead-letter"
}

resource "google_pubsub_subscription" "necesitados_events_dead_letter_sub" {
  name  = "necesitados-events-dead-letter-sub"
  topic = google_pubsub_topic.necesitados_events_dead_letter.name
}

#Creacion de Bucket
resource "google_storage_bucket" "bucket" {
  name          = "<AQUI HAY QUE PONER EL NOMBRE DEL BUCKET>"
  location      = "europe-west1"
  force_destroy = true
}