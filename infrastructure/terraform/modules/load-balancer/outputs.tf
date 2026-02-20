output "load_balancer_ip" {
  description = "Global static IP address of the load balancer"
  value       = google_compute_global_address.lb_ip.address
}

output "https_url" {
  description = "HTTPS URL of the application"
  value       = "https://${var.domain_name}"
}
