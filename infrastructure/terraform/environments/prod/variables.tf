variable "project_id" {
  type    = string
  default = "projectforge-4314f"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "domain_name" {
  type    = string
  default = "app.projectforge.app"
}

variable "db_tier" {
  type    = string
  default = "db-custom-2-4096"
}

variable "api_gateway_cpu" { type = string; default = "2" }
variable "api_gateway_memory" { type = string; default = "1Gi" }
variable "api_gateway_min" { type = number; default = 2 }
variable "api_gateway_max" { type = number; default = 10 }

variable "core_service_cpu" { type = string; default = "2" }
variable "core_service_memory" { type = string; default = "2Gi" }
variable "core_service_min" { type = number; default = 2 }
variable "core_service_max" { type = number; default = 10 }

variable "ai_service_cpu" { type = string; default = "4" }
variable "ai_service_memory" { type = string; default = "4Gi" }
variable "ai_service_min" { type = number; default = 1 }
variable "ai_service_max" { type = number; default = 5 }

variable "notification_cpu" { type = string; default = "1" }
variable "notification_memory" { type = string; default = "512Mi" }
variable "notification_min" { type = number; default = 1 }
variable "notification_max" { type = number; default = 3 }

variable "database_url" { type = string; sensitive = true }
variable "firebase_project_id" { type = string; default = "projectforge-4314f" }
variable "firebase_credentials" { type = string; sensitive = true }
variable "resend_api_key" { type = string; sensitive = true }
variable "slack_bot_token" { type = string; sensitive = true }
variable "db_password" { type = string; sensitive = true }
