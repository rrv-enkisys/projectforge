#!/bin/bash
SA="490835410559-compute@developer.gserviceaccount.com"
P="projectforge-4314f"
for r in roles/run.developer roles/cloudsql.client roles/secretmanager.secretAccessor roles/storage.objectAdmin roles/logging.viewer roles/monitoring.viewer; do
  gcloud projects add-iam-policy-binding "$P" --member="serviceAccount:$SA" --role="$r" --quiet && echo "OK: $r" || echo "FAIL: $r"
done
