output "documents_bucket_name" {
  description = "Name of the documents Cloud Storage bucket"
  value       = google_storage_bucket.documents.name
}

output "frontend_bucket_name" {
  description = "Name of the frontend Cloud Storage bucket"
  value       = google_storage_bucket.frontend.name
}

output "frontend_bucket_url" {
  description = "Public URL for the frontend bucket"
  value       = "https://storage.googleapis.com/${google_storage_bucket.frontend.name}"
}
