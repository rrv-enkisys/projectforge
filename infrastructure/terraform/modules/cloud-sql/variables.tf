variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC network self-link for private IP configuration"
  type        = string
}

variable "db_tier" {
  description = "Cloud SQL machine tier (e.g. db-f1-micro, db-custom-2-4096)"
  type        = string
  default     = "db-f1-micro"
}

variable "db_password" {
  description = "Password for the PostgreSQL app user"
  type        = string
  sensitive   = true
}
