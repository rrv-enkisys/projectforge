# ─── Static global IP ─────────────────────────────────────────────────────────

resource "google_compute_global_address" "lb_ip" {
  name    = "projectforge-lb-ip-${var.environment}"
  project = var.project_id
}

# ─── SSL Certificate (managed by Google) ──────────────────────────────────────

resource "google_compute_managed_ssl_certificate" "ssl" {
  name    = "projectforge-ssl-${var.environment}"
  project = var.project_id

  managed {
    domains = [var.domain_name]
  }
}

# ─── Cloud Armor WAF ──────────────────────────────────────────────────────────

resource "google_compute_security_policy" "waf" {
  name    = "projectforge-waf-${var.environment}"
  project = var.project_id

  # Rate limiting: throttle IPs exceeding 1000 req/min
  rule {
    action   = "throttle"
    priority = 1000
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 1000
        interval_sec = 60
      }
    }
    description = "Rate limit: 1000 req/min per IP"
  }

  # OWASP: block XSS
  rule {
    action   = "deny(403)"
    priority = 2000
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-stable')"
      }
    }
    description = "Block XSS attacks"
  }

  # OWASP: block SQL injection
  rule {
    action   = "deny(403)"
    priority = 2001
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-stable')"
      }
    }
    description = "Block SQL injection attacks"
  }

  # OWASP: block Remote File Inclusion
  rule {
    action   = "deny(403)"
    priority = 2002
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('rfi-stable')"
      }
    }
    description = "Block Remote File Inclusion"
  }

  # Default: allow all remaining traffic
  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }
}

# ─── Serverless NEG for API Gateway (Cloud Run) ───────────────────────────────

resource "google_compute_region_network_endpoint_group" "api_neg" {
  name                  = "projectforge-api-neg-${var.environment}"
  project               = var.project_id
  region                = var.region
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = var.api_gateway_service_name
  }
}

# ─── Backend: API Gateway ─────────────────────────────────────────────────────

resource "google_compute_backend_service" "api" {
  name                  = "projectforge-api-backend-${var.environment}"
  project               = var.project_id
  protocol              = "HTTPS"
  timeout_sec           = 30
  security_policy       = google_compute_security_policy.waf.id
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.api_neg.id
  }
}

# ─── Backend: Frontend (Cloud Storage) ───────────────────────────────────────

resource "google_compute_backend_bucket" "frontend" {
  name        = "projectforge-frontend-backend-${var.environment}"
  project     = var.project_id
  bucket_name = var.frontend_bucket_name
  enable_cdn  = true

  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    client_ttl        = 3600
    default_ttl       = 3600
    max_ttl           = 86400
    negative_caching  = true
    serve_while_stale = 86400
  }
}

# ─── URL Map ──────────────────────────────────────────────────────────────────

resource "google_compute_url_map" "url_map" {
  name            = "projectforge-url-map-${var.environment}"
  project         = var.project_id
  default_service = google_compute_backend_bucket.frontend.id

  host_rule {
    hosts        = [var.domain_name]
    path_matcher = "allpaths"
  }

  path_matcher {
    name            = "allpaths"
    default_service = google_compute_backend_bucket.frontend.id

    path_rule {
      paths   = ["/api/*"]
      service = google_compute_backend_service.api.id
    }
  }
}

# ─── HTTPS Proxy ──────────────────────────────────────────────────────────────

resource "google_compute_target_https_proxy" "https_proxy" {
  name             = "projectforge-https-proxy-${var.environment}"
  project          = var.project_id
  url_map          = google_compute_url_map.url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.ssl.id]
}

# ─── HTTP → HTTPS Redirect ────────────────────────────────────────────────────

resource "google_compute_url_map" "http_redirect" {
  name    = "projectforge-http-redirect-${var.environment}"
  project = var.project_id

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "projectforge-http-proxy-${var.environment}"
  project = var.project_id
  url_map = google_compute_url_map.http_redirect.id
}

# ─── Forwarding Rules ─────────────────────────────────────────────────────────

resource "google_compute_global_forwarding_rule" "https" {
  name                  = "projectforge-https-fwd-${var.environment}"
  project               = var.project_id
  ip_address            = google_compute_global_address.lb_ip.address
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  port_range            = "443"
  target                = google_compute_target_https_proxy.https_proxy.id
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "projectforge-http-fwd-${var.environment}"
  project               = var.project_id
  ip_address            = google_compute_global_address.lb_ip.address
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  port_range            = "80"
  target                = google_compute_target_http_proxy.http_proxy.id
}
