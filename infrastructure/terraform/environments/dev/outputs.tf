output "load_balancer_ip" {
  description = "Global IP of the load balancer — point your DNS A record here"
  value       = module.load_balancer.load_balancer_ip
}

output "https_url" {
  description = "Application HTTPS URL"
  value       = module.load_balancer.https_url
}

output "api_gateway_url" {
  description = "Internal Cloud Run URL for the API Gateway"
  value       = module.api_gateway.service_url
}

output "core_service_url" {
  description = "Internal Cloud Run URL for Core Service"
  value       = module.core_service.service_url
}

output "ai_service_url" {
  description = "Internal Cloud Run URL for AI Service"
  value       = module.ai_service.service_url
}

output "notification_service_url" {
  description = "Internal Cloud Run URL for Notification Service"
  value       = module.notification_service.service_url
}

output "cloud_sql_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = module.cloud_sql.private_ip_address
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name for proxy connections"
  value       = module.cloud_sql.instance_connection_name
}

output "documents_bucket" {
  description = "Cloud Storage bucket name for documents"
  value       = module.storage.documents_bucket_name
}

output "artifact_registry" {
  description = "Artifact Registry repository for Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/projectforge"
}
