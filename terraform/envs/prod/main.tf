locals {
  labels = {
    app         = "waybill"
    environment = var.environment
    managed_by  = "terraform"
  }
}

module "ingest_api_identity" {
  source              = "../../modules/workload-identity"
  project_id          = var.project_id
  account_id          = "ingest-api"
  display_name        = "waybill ingest-api (${var.environment})"
  k8s_namespace       = "waybill"
  k8s_service_account = "ingest-api"
}

# Identity Pub/Sub uses to sign push requests to tracker-worker.
resource "google_service_account" "pubsub_push" {
  project      = var.project_id
  account_id   = "pubsub-push"
  display_name = "Pub/Sub push invoker (${var.environment})"
}

module "scan_events" {
  source                     = "../../modules/event-topic"
  project_id                 = var.project_id
  name                       = "scan-events"
  push_endpoint              = var.tracker_push_endpoint
  push_service_account_email = google_service_account.pubsub_push.email
  labels                     = local.labels
}

# ingest-api may publish to this one topic. It holds no project-level role.
resource "google_pubsub_topic_iam_member" "ingest_api_publisher" {
  project = var.project_id
  topic   = module.scan_events.topic_name
  role    = "roles/pubsub.publisher"
  member  = module.ingest_api_identity.member
}

module "events_dataset" {
  source                    = "../../modules/events-dataset"
  project_id                = var.project_id
  dataset_id                = "waybill_raw"
  topic_id                  = module.scan_events.topic_id
  partition_expiration_days = var.partition_expiration_days
  deletion_protection       = var.deletion_protection
  reader_members            = var.analyst_members
  labels                    = local.labels
}

output "ingest_api_service_account" { value = module.ingest_api_identity.email }
output "scan_events_topic" { value = module.scan_events.topic_name }
output "raw_table" { value = "${module.events_dataset.dataset_id}.${module.events_dataset.table_id}" }
