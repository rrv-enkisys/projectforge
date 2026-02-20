resource "random_password" "secret_key" {
  length  = 64
  special = true
}

# ─── Secrets ──────────────────────────────────────────────────────────────────

resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url-${var.environment}"
  project   = var.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = var.database_url
}

resource "google_secret_manager_secret" "firebase_project_id" {
  secret_id = "firebase-project-id-${var.environment}"
  project   = var.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "firebase_project_id" {
  secret      = google_secret_manager_secret.firebase_project_id.id
  secret_data = var.firebase_project_id
}

resource "google_secret_manager_secret" "firebase_credentials" {
  secret_id = "firebase-credentials-${var.environment}"
  project   = var.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "firebase_credentials" {
  secret      = google_secret_manager_secret.firebase_credentials.id
  secret_data = var.firebase_credentials
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "secret-key-${var.environment}"
  project   = var.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret      = google_secret_manager_secret.secret_key.id
  secret_data = random_password.secret_key.result
}

resource "google_secret_manager_secret" "resend_api_key" {
  secret_id = "resend-api-key-${var.environment}"
  project   = var.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "resend_api_key" {
  secret      = google_secret_manager_secret.resend_api_key.id
  secret_data = var.resend_api_key
}

resource "google_secret_manager_secret" "slack_bot_token" {
  secret_id = "slack-bot-token-${var.environment}"
  project   = var.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "slack_bot_token" {
  secret      = google_secret_manager_secret.slack_bot_token.id
  secret_data = var.slack_bot_token
}

resource "google_secret_manager_secret" "cloud_sql_password" {
  secret_id = "cloud-sql-password-${var.environment}"
  project   = var.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "cloud_sql_password" {
  secret      = google_secret_manager_secret.cloud_sql_password.id
  secret_data = var.db_password
}

# ─── IAM bindings: database_url ───────────────────────────────────────────────

resource "google_secret_manager_secret_iam_member" "database_url_core" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.core_service_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "database_url_ai" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.ai_service_sa_email}"
}

# ─── IAM bindings: firebase_credentials ──────────────────────────────────────

resource "google_secret_manager_secret_iam_member" "firebase_creds_gateway" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.firebase_credentials.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.api_gateway_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "firebase_creds_core" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.firebase_credentials.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.core_service_sa_email}"
}

# ─── IAM bindings: firebase_project_id ───────────────────────────────────────

resource "google_secret_manager_secret_iam_member" "firebase_pid_gateway" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.firebase_project_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.api_gateway_sa_email}"
}

# ─── IAM bindings: secret_key ─────────────────────────────────────────────────

resource "google_secret_manager_secret_iam_member" "secret_key_core" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.core_service_sa_email}"
}

# ─── IAM bindings: resend_api_key ─────────────────────────────────────────────

resource "google_secret_manager_secret_iam_member" "resend_notification" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.resend_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.notification_service_sa_email}"
}

# ─── IAM bindings: slack_bot_token ────────────────────────────────────────────

resource "google_secret_manager_secret_iam_member" "slack_notification" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.slack_bot_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.notification_service_sa_email}"
}
