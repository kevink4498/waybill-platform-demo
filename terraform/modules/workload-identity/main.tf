# One GCP service account per Kubernetes service account, bound through GKE Workload
# Identity. No service-account keys are created anywhere in this repository.

variable "project_id" { type = string }
variable "account_id" { type = string }
variable "display_name" { type = string }
variable "k8s_namespace" { type = string }
variable "k8s_service_account" { type = string }

resource "google_service_account" "this" {
  project      = var.project_id
  account_id   = var.account_id
  display_name = var.display_name
}

resource "google_service_account_iam_member" "workload_identity" {
  service_account_id = google_service_account.this.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.k8s_namespace}/${var.k8s_service_account}]"
}

output "email" { value = google_service_account.this.email }
output "member" { value = "serviceAccount:${google_service_account.this.email}" }
