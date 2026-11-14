# BigQuery landing dataset: a day-partitioned raw table fed straight from Pub/Sub,
# with partition expiry so retention is enforced by the platform, not by a cron job.

variable "project_id" { type = string }
variable "dataset_id" { type = string }
variable "location" {
  type    = string
  default = "EU"
}
variable "topic_id" { type = string }
variable "partition_expiration_days" {
  type    = number
  default = 365
}
variable "deletion_protection" {
  type    = bool
  default = true
}
variable "reader_members" {
  type    = list(string)
  default = []
}
variable "labels" {
  type    = map(string)
  default = {}
}

data "google_project" "this" {
  project_id = var.project_id
}

resource "google_bigquery_dataset" "this" {
  project    = var.project_id
  dataset_id = var.dataset_id
  location   = var.location
  labels     = var.labels
}

resource "google_bigquery_table" "scan_events_raw" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.this.dataset_id
  table_id            = "scan_events_raw"
  deletion_protection = var.deletion_protection
  labels              = var.labels

  time_partitioning {
    type          = "DAY"
    field         = "publish_time"
    expiration_ms = var.partition_expiration_days * 24 * 60 * 60 * 1000
  }
  clustering = ["message_id"]

  schema = jsonencode([
    { name = "subscription_name", type = "STRING", mode = "NULLABLE" },
    { name = "message_id", type = "STRING", mode = "NULLABLE" },
    { name = "publish_time", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "data", type = "JSON", mode = "NULLABLE" },
    { name = "attributes", type = "JSON", mode = "NULLABLE" },
  ])
}

locals {
  pubsub_agent = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# Dataset-scoped, not project-scoped: the service agent can write here and nowhere else.
resource "google_bigquery_dataset_iam_member" "pubsub_writer" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.this.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = local.pubsub_agent
}

resource "google_bigquery_dataset_iam_member" "readers" {
  for_each   = toset(var.reader_members)
  project    = var.project_id
  dataset_id = google_bigquery_dataset.this.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = each.value
}

resource "google_pubsub_subscription" "to_bigquery" {
  project = var.project_id
  name    = "${var.dataset_id}-scan-events-bq"
  topic   = var.topic_id
  labels  = var.labels

  bigquery_config {
    table          = "${var.project_id}.${google_bigquery_dataset.this.dataset_id}.${google_bigquery_table.scan_events_raw.table_id}"
    write_metadata = true
  }

  expiration_policy { ttl = "" }
  depends_on = [google_bigquery_dataset_iam_member.pubsub_writer]
}

output "dataset_id" { value = google_bigquery_dataset.this.dataset_id }
output "table_id" { value = google_bigquery_table.scan_events_raw.table_id }
