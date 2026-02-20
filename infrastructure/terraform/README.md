# ProjectForge — Terraform GCP Infrastructure

Complete Terraform configuration for deploying ProjectForge to Google Cloud Platform.

## Architecture

```
Internet
    ↓
Cloud Load Balancer (HTTPS + Cloud Armor WAF)
    ├── /*     → Cloud Storage (frontend, React SPA)
    └── /api/* → API Gateway (Cloud Run, Go, port 8080)
                      ↓
          ┌───────────┼───────────┐
          ↓           ↓           ↓
     Core Service  AI Service  Notification Service
     (Cloud Run)  (Cloud Run)  (Cloud Run)
     port 8081    port 8082    port 8083
          │           │
          └─────┬─────┘
                ↓
         Cloud SQL (PostgreSQL 15 + pgvector)
         [Private IP via Serverless VPC Connector]
```

## Module Structure

```
infrastructure/terraform/
├── backend.tf                    # GCS remote state config
├── versions.tf                   # Provider version constraints
├── modules/
│   ├── vpc/                      # VPC, subnet, NAT, VPC Connector, PSC
│   ├── iam/                      # Service accounts + least-privilege roles
│   ├── secret-manager/           # 7 secrets + per-SA IAM bindings
│   ├── cloud-sql/                # PostgreSQL 15, Private IP, backups
│   ├── cloud-storage/            # Documents bucket + frontend SPA bucket
│   ├── cloud-run/                # Reusable Cloud Run v2 service module
│   └── load-balancer/            # HTTPS LB + Cloud Armor WAF + CDN
└── environments/
    ├── dev/                      # Minimal cost, ai/notification scale to 0
    ├── staging/                  # Mid-tier, all services always on
    └── prod/                     # HA sizing, deletion protection enabled
```

## Prerequisites

### 1. Bootstrap the Terraform state bucket

This must be done **once before any `terraform init`**:

```bash
gsutil mb -p projectforge-4314f -l us-central1 gs://projectforge-terraform-state
gsutil versioning set on gs://projectforge-terraform-state
```

### 2. Authenticate with GCP

```bash
gcloud auth application-default login
gcloud config set project projectforge-4314f
```

### 3. Create your secrets file

```bash
cd environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with non-secret values

cat > secrets.tfvars <<'EOF'
database_url         = "postgresql+asyncpg://app:PASSWORD@CLOUD_SQL_PRIVATE_IP/projectforge"
firebase_credentials = "<base64-encoded service account JSON>"
resend_api_key       = "re_xxxxxxxxxxxx"
slack_bot_token      = "xoxb-xxxxxxxxxxxx"
db_password          = "your-strong-password"
EOF
```

`secrets.tfvars` is in `.gitignore` and must **never** be committed.

## Deployment Order

The first deployment must be done in stages because Docker images must exist before Cloud Run services can be created:

### Stage 1 — Bootstrap Artifact Registry

```bash
cd environments/dev
terraform init
terraform apply -target=google_artifact_registry_repository.docker \
                -target=google_project_service.apis \
                -var-file=secrets.tfvars
```

### Stage 2 — Build and push Docker images

```bash
PROJECT=projectforge-4314f
REGION=us-central1
REPO="$REGION-docker.pkg.dev/$PROJECT/projectforge"

gcloud builds submit ../../apps/api-gateway \
  --tag "$REPO/api-gateway:latest"

gcloud builds submit ../../apps/core-service \
  --tag "$REPO/core-service:latest"

gcloud builds submit ../../apps/ai-service \
  --tag "$REPO/ai-service:latest"

gcloud builds submit ../../apps/notification-service \
  --tag "$REPO/notification-service:latest"
```

### Stage 3 — Full apply

```bash
terraform apply -var-file=secrets.tfvars -parallelism=1
```

> `parallelism=1` is recommended on first apply because the VPC peering
> connection (`servicenetworking.googleapis.com`) can conflict with concurrent
> resource creation.

### Subsequent deploys

```bash
terraform apply -var-file=secrets.tfvars
```

## Post-Deployment

### Install pgvector extension

Connect to Cloud SQL and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Run database migrations

```bash
# From your dev machine via Cloud SQL Auth Proxy:
cloud-sql-proxy projectforge-4314f:us-central1:projectforge-dev

# Then from apps/core-service:
alembic upgrade head
```

### Point DNS to the load balancer

```bash
terraform output load_balancer_ip
# Add an A record for your domain pointing to this IP
```

## Environments

| Environment | Domain | DB Tier | AI/Notif min instances |
|------------|--------|---------|----------------------|
| `dev` | dev.projectforge.app | db-f1-micro | 0 (scale to zero) |
| `staging` | staging.projectforge.app | db-g1-small | 1 |
| `prod` | app.projectforge.app | db-custom-2-4096 | 1 |

## Useful Commands

```bash
# Validate configuration
terraform validate

# Format all files
terraform fmt -recursive

# Plan without applying
terraform plan -var-file=secrets.tfvars

# Destroy a specific resource (careful!)
terraform destroy -target=module.ai_service -var-file=secrets.tfvars

# Show current state
terraform show

# View outputs
terraform output
```

## Security Notes

- All Cloud Run services use `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` — they are not directly accessible from the internet
- Cloud SQL has no public IP (`ipv4_enabled = false`)
- Cloud Armor WAF protects against XSS, SQLi, RFI, and rate-limits at 1000 req/min per IP
- Service accounts follow least-privilege (no broad `editor` or `owner` roles)
- Secrets are stored in Secret Manager; each SA only has access to the secrets it needs
- `deletion_protection = true` is enabled for Cloud SQL in production
