terraform {
  required_version = ">= 1.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # One state per environment, so a mistake in dev can never touch prod state.
  backend "gcs" {
    bucket = "waybill-tfstate-dev"
    prefix = "platform"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
