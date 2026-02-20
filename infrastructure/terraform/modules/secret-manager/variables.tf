variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "core_service_sa_email" {
  description = "Service account email for core-service"
  type        = string
}

variable "ai_service_sa_email" {
  description = "Service account email for ai-service"
  type        = string
}

variable "notification_service_sa_email" {
  description = "Service account email for notification-service"
  type        = string
}

variable "api_gateway_sa_email" {
  description = "Service account email for api-gateway"
  type        = string
}

# ─── Sensitive secret values ──────────────────────────────────────────────────
# Pass these via TF_VAR_* environment variables or a secrets.tfvars file
# that is listed in .gitignore. NEVER commit actual secret values.

variable "database_url" {
  description = "PostgreSQL connection URL (postgresql+asyncpg://...)"
  type        = string
  sensitive   = true
}

variable "firebase_project_id" {
  description = "Firebase / GCP project ID"
  type        = string
}

variable "firebase_credentials" {
  description = "Firebase service account JSON (raw or base64-encoded)"
  type        = string
  sensitive   = true
}

variable "resend_api_key" {
  description = "Resend.com API key for transactional email"
  type        = string
  sensitive   = true
}

variable "slack_bot_token" {
  description = "Slack bot OAuth token"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL app user password (used to construct database_url)"
  type        = string
  sensitive   = true
}
