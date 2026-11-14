# A Pub/Sub topic with a push subscription, retry policy and a dead-letter topic.

variable "project_id" { type = string }
variable "name" { type = string }
variable "push_endpoint" { type = string }
variable "push_service_account_email" { type = string }
variable "max_delivery_attempts" {
  type    = number
  default = 5
}
variable "message_retention" {
  type    = string
  default = "604800s" # 7 days
}
variable "labels" {
  type    = map(string)
  default = {}
}

data "google_project" "this" {
  project_id = var.project_id
}

resource "google_pubsub_topic" "main" {
  project                    = var.project_id
  name                       = var.name
  message_retention_duration = var.message_retention
  labels                     = var.labels
}

resource "google_pubsub_topic" "dead_letter" {
  project = var.project_id
  name    = "${var.name}-dlq"
  labels  = var.labels
}

# Keeps dead-lettered messages until someone inspects or replays them.
resource "google_pubsub_subscription" "dead_letter_hold" {
  project                    = var.project_id
  name                       = "${var.name}-dlq-hold"
  topic                      = google_pubsub_topic.dead_letter.id
  message_retention_duration = "1209600s" # 14 days
  expiration_policy { ttl = "" }
  labels = var.labels
}

resource "google_pubsub_subscription" "push" {
  project              = var.project_id
  name                 = "${var.name}-push"
  topic                = google_pubsub_topic.main.id
  ack_deadline_seconds = 30
  labels               = var.labels

  push_config {
    push_endpoint = var.push_endpoint
    oidc_token {
      service_account_email = var.push_service_account_email
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = var.max_delivery_attempts
  }

  expiration_policy { ttl = "" }
}

# The Pub/Sub service agent must be allowed to forward to the DLQ and ack the source.
locals {
  pubsub_agent = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "dlq_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.dead_letter.name
  role    = "roles/pubsub.publisher"
  member  = local.pubsub_agent
}

resource "google_pubsub_subscription_iam_member" "source_subscriber" {
  project      = var.project_id
  subscription = google_pubsub_subscription.push.name
  role         = "roles/pubsub.subscriber"
  member       = local.pubsub_agent
}

output "topic_name" { value = google_pubsub_topic.main.name }
output "topic_id" { value = google_pubsub_topic.main.id }
output "dead_letter_topic_name" { value = google_pubsub_topic.dead_letter.name }
