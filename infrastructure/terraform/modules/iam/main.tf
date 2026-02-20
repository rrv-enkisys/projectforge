locals {
  env = var.environment
}

# ─── Service Accounts ─────────────────────────────────────────────────────────

resource "google_service_account" "api_gateway" {
  account_id   = "sa-api-gateway-${local.env}"
  display_name = "API Gateway Service Account (${local.env})"
  project      = var.project_id
}

resource "google_service_account" "core_service" {
  account_id   = "sa-core-service-${local.env}"
  display_name = "Core Service Service Account (${local.env})"
  project      = var.project_id
}

resource "google_service_account" "ai_service" {
  account_id   = "sa-ai-service-${local.env}"
  display_name = "AI Service Service Account (${local.env})"
  project      = var.project_id
}

resource "google_service_account" "notification_service" {
  account_id   = "sa-notification-${local.env}"
  display_name = "Notification Service Service Account (${local.env})"
  project      = var.project_id
}

resource "google_service_account" "cloud_build" {
  account_id   = "sa-cloud-build-${local.env}"
  display_name = "Cloud Build Service Account (${local.env})"
  project      = var.project_id
}

# ─── API Gateway roles ────────────────────────────────────────────────────────
# Can invoke other Cloud Run services

resource "google_project_iam_member" "api_gateway_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.api_gateway.email}"
}

# ─── Core Service roles ───────────────────────────────────────────────────────

resource "google_project_iam_member" "core_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.core_service.email}"
}

resource "google_project_iam_member" "core_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.core_service.email}"
}

# ─── AI Service roles ─────────────────────────────────────────────────────────

resource "google_project_iam_member" "ai_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.ai_service.email}"
}

resource "google_project_iam_member" "ai_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.ai_service.email}"
}

resource "google_project_iam_member" "ai_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.ai_service.email}"
}

resource "google_project_iam_member" "ai_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ai_service.email}"
}

# ─── Notification Service roles ───────────────────────────────────────────────

resource "google_project_iam_member" "notification_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.notification_service.email}"
}

# ─── Cloud Build roles ────────────────────────────────────────────────────────

resource "google_project_iam_member" "build_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

resource "google_project_iam_member" "build_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

resource "google_project_iam_member" "build_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

resource "google_project_iam_member" "build_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}
