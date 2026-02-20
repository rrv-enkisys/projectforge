output "load_balancer_ip" {
  description = "Global IP — point your DNS A record here"
  value       = module.load_balancer.load_balancer_ip
}

output "https_url" {
  value = module.load_balancer.https_url
}

output "api_gateway_url" {
  value = module.api_gateway.service_url
}

output "cloud_sql_private_ip" {
  value = module.cloud_sql.private_ip_address
}

output "cloud_sql_connection_name" {
  value = module.cloud_sql.instance_connection_name
}
