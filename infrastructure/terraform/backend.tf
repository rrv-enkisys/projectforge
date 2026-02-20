# Remote state stored in GCS.
# The bucket must be created MANUALLY before running terraform init:
#   gsutil mb -p projectforge-4314f -l us-central1 gs://projectforge-terraform-state
#   gsutil versioning set on gs://projectforge-terraform-state

terraform {
  backend "gcs" {
    bucket = "projectforge-terraform-state"
    prefix = "terraform/state"
  }
}
