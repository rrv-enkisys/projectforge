# ─── Project & region ─────────────────────────────────────────────────────────

variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "projectforge-4314f"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "domain_name" {
  description = "Primary domain for the application"
  type        = string
  default     = "dev.projectforge.app"
}

# ─── Cloud SQL ────────────────────────────────────────────────────────────────

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

# ─── Cloud Run: API Gateway ───────────────────────────────────────────────────

variable "api_gateway_cpu" {
  type    = string
  default = "1"
}

variable "api_gateway_memory" {
  type    = string
  default = "512Mi"
}

variable "api_gateway_min" {
  type    = number
  default = 1
}

variable "api_gateway_max" {
  type    = number
  default = 3
}

# ─── Cloud Run: Core Service ──────────────────────────────────────────────────

variable "core_service_cpu" {
  type    = string
  default = "1"
}

variable "core_service_memory" {
  type    = string
  default = "1Gi"
}

variable "core_service_min" {
  type    = number
  default = 1
}

variable "core_service_max" {
  type    = number
  default = 3
}

# ─── Cloud Run: AI Service ────────────────────────────────────────────────────

variable "ai_service_cpu" {
  type    = string
  default = "2"
}

variable "ai_service_memory" {
  type    = string
  default = "2Gi"
}

variable "ai_service_min" {
  description = "Scales to 0 in dev to save costs"
  type        = number
  default     = 0
}

variable "ai_service_max" {
  type    = number
  default = 2
}

# ─── Cloud Run: Notification Service ─────────────────────────────────────────

variable "notification_cpu" {
  type    = string
  default = "0.5"
}

variable "notification_memory" {
  type    = string
  default = "256Mi"
}

variable "notification_min" {
  description = "Scales to 0 in dev to save costs"
  type        = number
  default     = 0
}

variable "notification_max" {
  type    = number
  default = 2
}

# ─── Secrets (sensitive — pass via TF_VAR_* or secrets.tfvars) ───────────────

variable "database_url" {
  description = "PostgreSQL connection URL"
  type        = string
  sensitive   = true
}

variable "firebase_project_id" {
  description = "Firebase project ID"
  type        = string
  default     = "projectforge-4314f"
}

variable "firebase_credentials" {
  description = "Firebase service account JSON"
  type        = string
  sensitive   = true
}

variable "resend_api_key" {
  description = "Resend.com API key"
  type        = string
  sensitive   = true
}

variable "slack_bot_token" {
  description = "Slack bot OAuth token"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL app user password"
  type        = string
  sensitive   = true
}
