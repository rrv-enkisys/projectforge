variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "name" {
  description = "Cloud Run service name"
  type        = string
}

variable "image" {
  description = "Docker image URI (Artifact Registry)"
  type        = string
}

variable "port" {
  description = "Container port the service listens on"
  type        = number
  default     = 8080
}

variable "cpu" {
  description = "CPU limit (e.g. '1', '2')"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory limit (e.g. '512Mi', '1Gi')"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimum number of instances (0 to scale to zero)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 5
}

variable "service_account_email" {
  description = "Service account email to attach to the Cloud Run service"
  type        = string
}

variable "vpc_connector_id" {
  description = "Serverless VPC connector ID for private networking"
  type        = string
}

variable "allow_public" {
  description = "Whether to allow unauthenticated (public) invocations"
  type        = bool
  default     = false
}

variable "env_vars" {
  description = "Plain environment variables as key-value map"
  type        = map(string)
  default     = {}
}

variable "secret_env_vars" {
  description = "Environment variables sourced from Secret Manager"
  type = list(object({
    name   = string
    secret = string
  }))
  default = []
}
