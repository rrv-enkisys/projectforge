resource "google_compute_network" "vpc" {
  name                    = "projectforge-${var.environment}"
  project                 = var.project_id
  auto_create_subnetworks = false
  description             = "ProjectForge VPC (${var.environment})"
}

resource "google_compute_subnetwork" "private" {
  name                     = "projectforge-private-${var.environment}"
  project                  = var.project_id
  region                   = var.region
  network                  = google_compute_network.vpc.id
  ip_cidr_range            = var.vpc_cidr
  private_ip_google_access = true
}

resource "google_compute_router" "router" {
  name    = "projectforge-router-${var.environment}"
  project = var.project_id
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "projectforge-nat-${var.environment}"
  project                            = var.project_id
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Serverless VPC Connector — allows Cloud Run to reach Cloud SQL via private IP
resource "google_vpc_access_connector" "connector" {
  name    = "pf-connector-${var.environment}"
  project = var.project_id
  region  = var.region
  network = google_compute_network.vpc.name

  ip_cidr_range = "10.8.0.0/28"
  min_instances = 2
  max_instances = 3
  machine_type  = var.environment == "prod" ? "e2-standard-4" : "f1-micro"
}

# Global IP range allocated for Private Service Connect (Cloud SQL private IP)
resource "google_compute_global_address" "private_service_range" {
  name          = "projectforge-psa-${var.environment}"
  project       = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

# VPC peering to Google managed services (required for Cloud SQL private IP)
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_range.name]
}
