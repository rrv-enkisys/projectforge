resource "google_sql_database_instance" "main" {
  name             = "projectforge-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  # Prevent accidental deletion in production
  deletion_protection = var.environment == "prod" ? true : false

  settings {
    tier = var.db_tier

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "prod" ? true : false
      transaction_log_retention_days = var.environment == "prod" ? 7 : 1
      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 14 : 3
      }
    }

    ip_configuration {
      ipv4_enabled                                  = false # No public IP
      private_network                               = var.vpc_id
      enable_private_path_for_google_cloud_services = true
    }

    database_flags {
      name  = "max_connections"
      value = var.environment == "prod" ? "200" : "50"
    }

    # pgvector is installed as a PostgreSQL extension via migration SQL:
    # CREATE EXTENSION IF NOT EXISTS vector;
    # Cloud SQL PostgreSQL 15 supports pgvector natively since 2023.

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 4 # 04:00 UTC
      update_track = "stable"
    }
  }
}

resource "google_sql_database" "projectforge" {
  name     = "projectforge"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

resource "google_sql_user" "app" {
  name     = "app"
  instance = google_sql_database_instance.main.name
  password = var.db_password
  project  = var.project_id
}
