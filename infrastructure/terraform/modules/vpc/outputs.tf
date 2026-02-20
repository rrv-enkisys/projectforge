output "vpc_id" {
  description = "VPC network self-link"
  value       = google_compute_network.vpc.id
}

output "vpc_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "subnet_id" {
  description = "Private subnet self-link"
  value       = google_compute_subnetwork.private.id
}

output "vpc_connector_id" {
  description = "Serverless VPC Connector ID for Cloud Run vpc_access"
  value       = google_vpc_access_connector.connector.id
}

output "vpc_connector_name" {
  description = "Serverless VPC Connector name"
  value       = google_vpc_access_connector.connector.name
}
