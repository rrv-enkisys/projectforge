output "database_url_secret_id" {
  description = "Secret Manager resource ID for database-url"
  value       = google_secret_manager_secret.database_url.id
}

output "firebase_project_id_secret_id" {
  description = "Secret Manager resource ID for firebase-project-id"
  value       = google_secret_manager_secret.firebase_project_id.id
}

output "firebase_credentials_secret_id" {
  description = "Secret Manager resource ID for firebase-credentials"
  value       = google_secret_manager_secret.firebase_credentials.id
}

output "secret_key_secret_id" {
  description = "Secret Manager resource ID for secret-key"
  value       = google_secret_manager_secret.secret_key.id
}

output "resend_api_key_secret_id" {
  description = "Secret Manager resource ID for resend-api-key"
  value       = google_secret_manager_secret.resend_api_key.id
}

output "slack_bot_token_secret_id" {
  description = "Secret Manager resource ID for slack-bot-token"
  value       = google_secret_manager_secret.slack_bot_token.id
}

output "cloud_sql_password_secret_id" {
  description = "Secret Manager resource ID for cloud-sql-password"
  value       = google_secret_manager_secret.cloud_sql_password.id
}
