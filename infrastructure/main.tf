terraform {
required_version = ">= 1.5.0"
required_providers { google = { source = "hashicorp/google", version = "~> 5.35" } }
}
provider "google" { project = var.project_id, region = var.region }

Enable APIs, bucket, Artifact Registry, SA will be added in Module 5.

