variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "europe-west1"
}
variable "environment" { type = string }
variable "tracker_push_endpoint" { type = string }
variable "partition_expiration_days" { type = number }
variable "deletion_protection" { type = bool }
variable "analyst_members" {
  type    = list(string)
  default = []
}
