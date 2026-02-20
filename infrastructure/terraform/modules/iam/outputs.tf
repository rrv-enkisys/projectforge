output "api_gateway_sa_email" {
  description = "API Gateway service account email"
  value       = google_service_account.api_gateway.email
}

output "core_service_sa_email" {
  description = "Core Service service account email"
  value       = google_service_account.core_service.email
}

output "ai_service_sa_email" {
  description = "AI Service service account email"
  value       = google_service_account.ai_service.email
}

output "notification_service_sa_email" {
  description = "Notification Service service account email"
  value       = google_service_account.notification_service.email
}

output "cloud_build_sa_email" {
  description = "Cloud Build service account email"
  value       = google_service_account.cloud_build.email
}
