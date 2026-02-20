# ─── Documents Bucket ─────────────────────────────────────────────────────────

resource "google_storage_bucket" "documents" {
  name          = "projectforge-documents-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["Content-Type", "Authorization"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  versioning {
    enabled = var.environment == "prod"
  }
}

# ─── Frontend Bucket (SPA) ────────────────────────────────────────────────────

resource "google_storage_bucket" "frontend" {
  name          = "projectforge-frontend-${var.environment}"
  location      = "US" # Multi-regional for CDN performance
  project       = var.project_id
  force_destroy = true

  # SPA routing: all unknown paths serve index.html
  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }

  # uniform_bucket_level_access = true required by org policy
  # Public access is granted via IAM binding (allUsers objectViewer) below
  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type", "Cache-Control"]
    max_age_seconds = 3600
  }
}

resource "google_storage_bucket_iam_member" "frontend_public" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
