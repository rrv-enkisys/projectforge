variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for the documents bucket"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "cors_origins" {
  description = "Allowed CORS origins for the documents bucket"
  type        = list(string)
  default     = ["*"]
}
