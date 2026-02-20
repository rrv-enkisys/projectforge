variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region (used for Cloud Run NEG)"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "domain_name" {
  description = "Primary domain name (e.g. app.projectforge.app)"
  type        = string
}

variable "api_gateway_service_name" {
  description = "Cloud Run service name for the API gateway"
  type        = string
}

variable "frontend_bucket_name" {
  description = "Cloud Storage bucket name serving the frontend static files"
  type        = string
}
