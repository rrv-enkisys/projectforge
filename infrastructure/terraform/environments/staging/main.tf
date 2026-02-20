terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "gcs" {
    bucket = "projectforge-terraform-state"
    prefix = "terraform/state/staging"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

locals {
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "aiplatform.googleapis.com",
    "documentai.googleapis.com",
    "pubsub.googleapis.com",
    "cloudtasks.googleapis.com",
    "firestore.googleapis.com",
  ])
  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

module "iam" {
  source      = "../../modules/iam"
  project_id  = local.project_id
  environment = local.environment
  depends_on  = [google_project_service.apis]
}

module "vpc" {
  source      = "../../modules/vpc"
  project_id  = local.project_id
  region      = local.region
  environment = local.environment
  depends_on  = [google_project_service.apis]
}

module "secrets" {
  source                        = "../../modules/secret-manager"
  project_id                    = local.project_id
  environment                   = local.environment
  core_service_sa_email         = module.iam.core_service_sa_email
  ai_service_sa_email           = module.iam.ai_service_sa_email
  notification_service_sa_email = module.iam.notification_service_sa_email
  api_gateway_sa_email          = module.iam.api_gateway_sa_email
  database_url                  = var.database_url
  firebase_project_id           = var.firebase_project_id
  firebase_credentials          = var.firebase_credentials
  resend_api_key                = var.resend_api_key
  slack_bot_token               = var.slack_bot_token
  db_password                   = var.db_password
  depends_on                    = [module.iam, google_project_service.apis]
}

module "cloud_sql" {
  source      = "../../modules/cloud-sql"
  project_id  = local.project_id
  region      = local.region
  environment = local.environment
  vpc_id      = module.vpc.vpc_id
  db_tier     = var.db_tier
  db_password = var.db_password
  depends_on  = [module.vpc]
}

module "storage" {
  source       = "../../modules/cloud-storage"
  project_id   = local.project_id
  region       = local.region
  environment  = local.environment
  cors_origins = ["https://${var.domain_name}"]
  depends_on   = [google_project_service.apis]
}

module "core_service" {
  source                = "../../modules/cloud-run"
  project_id            = local.project_id
  region                = local.region
  name                  = "core-service-${local.environment}"
  image                 = "${local.region}-docker.pkg.dev/${local.project_id}/projectforge/core-service:latest"
  port                  = 8081
  cpu                   = var.core_service_cpu
  memory                = var.core_service_memory
  min_instances         = var.core_service_min
  max_instances         = var.core_service_max
  service_account_email = module.iam.core_service_sa_email
  vpc_connector_id      = module.vpc.vpc_connector_id
  allow_public          = false
  env_vars = {
    PORT                = "8081"
    ENV                 = local.environment
    DEBUG               = "false"
    CORS_ORIGINS        = "https://${var.domain_name}"
    FIREBASE_PROJECT_ID = var.firebase_project_id
  }
  secret_env_vars = [
    { name = "DATABASE_URL", secret = module.secrets.database_url_secret_id },
    { name = "SECRET_KEY", secret = module.secrets.secret_key_secret_id },
    { name = "FIREBASE_CREDENTIALS_PATH", secret = module.secrets.firebase_credentials_secret_id },
  ]
  depends_on = [module.cloud_sql, module.secrets, module.vpc]
}

module "ai_service" {
  source                = "../../modules/cloud-run"
  project_id            = local.project_id
  region                = local.region
  name                  = "ai-service-${local.environment}"
  image                 = "${local.region}-docker.pkg.dev/${local.project_id}/projectforge/ai-service:latest"
  port                  = 8082
  cpu                   = var.ai_service_cpu
  memory                = var.ai_service_memory
  min_instances         = var.ai_service_min
  max_instances         = var.ai_service_max
  service_account_email = module.iam.ai_service_sa_email
  vpc_connector_id      = module.vpc.vpc_connector_id
  allow_public          = false
  env_vars = {
    PORT                   = "8082"
    environment            = local.environment
    gcp_project_id         = local.project_id
    gcp_location           = local.region
    gcs_bucket_name        = module.storage.documents_bucket_name
    vertex_embedding_model = "text-embedding-004"
    vertex_llm_model       = "gemini-2.0-flash"
  }
  secret_env_vars = [
    { name = "DATABASE_URL", secret = module.secrets.database_url_secret_id },
  ]
  depends_on = [module.cloud_sql, module.secrets, module.storage, module.vpc]
}

module "notification_service" {
  source                = "../../modules/cloud-run"
  project_id            = local.project_id
  region                = local.region
  name                  = "notification-service-${local.environment}"
  image                 = "${local.region}-docker.pkg.dev/${local.project_id}/projectforge/notification-service:latest"
  port                  = 8083
  cpu                   = var.notification_cpu
  memory                = var.notification_memory
  min_instances         = var.notification_min
  max_instances         = var.notification_max
  service_account_email = module.iam.notification_service_sa_email
  vpc_connector_id      = module.vpc.vpc_connector_id
  allow_public          = false
  env_vars = {
    PORT        = "8083"
    ENVIRONMENT = local.environment
  }
  secret_env_vars = [
    { name = "RESEND_API_KEY", secret = module.secrets.resend_api_key_secret_id },
    { name = "SLACK_BOT_TOKEN", secret = module.secrets.slack_bot_token_secret_id },
  ]
  depends_on = [module.secrets, module.vpc]
}

module "api_gateway" {
  source                = "../../modules/cloud-run"
  project_id            = local.project_id
  region                = local.region
  name                  = "api-gateway-${local.environment}"
  image                 = "${local.region}-docker.pkg.dev/${local.project_id}/projectforge/api-gateway:latest"
  port                  = 8080
  cpu                   = var.api_gateway_cpu
  memory                = var.api_gateway_memory
  min_instances         = var.api_gateway_min
  max_instances         = var.api_gateway_max
  service_account_email = module.iam.api_gateway_sa_email
  vpc_connector_id      = module.vpc.vpc_connector_id
  allow_public          = false
  env_vars = {
    ENVIRONMENT              = local.environment
    PORT                     = "8080"
    CORE_SERVICE_URL         = module.core_service.service_url
    AI_SERVICE_URL           = module.ai_service.service_url
    NOTIFICATION_SERVICE_URL = module.notification_service.service_url
    CORS_ORIGINS             = "https://${var.domain_name}"
    RATE_LIMIT_RPS           = "100"
  }
  secret_env_vars = [
    { name = "FIREBASE_PROJECT_ID", secret = module.secrets.firebase_project_id_secret_id },
    { name = "FIREBASE_CREDENTIALS", secret = module.secrets.firebase_credentials_secret_id },
  ]
  depends_on = [module.vpc, module.secrets, module.core_service, module.ai_service, module.notification_service]
}

module "load_balancer" {
  source                   = "../../modules/load-balancer"
  project_id               = local.project_id
  region                   = local.region
  environment              = local.environment
  domain_name              = var.domain_name
  api_gateway_service_name = module.api_gateway.service_name
  frontend_bucket_name     = module.storage.frontend_bucket_name
  depends_on               = [module.api_gateway, module.storage]
}
