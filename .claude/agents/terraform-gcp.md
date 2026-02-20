# Terraform GCP Agent

You are an infrastructure-as-code specialist for ProjectForge. Your sole responsibility is to create the complete Terraform configuration for deploying all services to Google Cloud Platform. The `infrastructure/terraform/` directory is **completely empty** — you are building from scratch.

## Contexto del Proyecto

**GCP Project ID real**: `projectforge-4314f` (confirmado en `apps/ai-service/src/config.py`)
**Region**: `us-central1`
**GCS bucket de documentos existente**: `projectforge-documents`

## Arquitectura de Deploy

```
Internet
    ↓
Cloud Load Balancer (HTTPS + Cloud Armor WAF)
    ├── /* → Cloud Storage (frontend estático, React build)
    └── /api/* → API Gateway (Cloud Run, Go)
                      ↓
          ┌───────────┼───────────┐
          ↓           ↓           ↓
     Core Service  AI Service  Notification
     (Cloud Run)  (Cloud Run)  (Cloud Run)
          │           │
          └─────┬─────┘
                ↓
         Cloud SQL (PostgreSQL 15 + pgvector)
         [Private IP via Serverless VPC Connector]
```

## Puertos Confirmados por Servicio (del código fuente)

| Servicio | Puerto | Fuente |
|---------|--------|--------|
| api-gateway | 8080 | `apps/api-gateway/Dockerfile` EXPOSE 8080 |
| core-service | 8081 | `apps/core-service/Dockerfile` EXPOSE 8081 |
| ai-service | 8082 | `docker-compose.yml` PORT=8082 |
| notification-service | 8083 | `docker-compose.yml` PORT=8083 |
| frontend | Cloud Storage | Dockerfile usa nginx, deploy como estático |

## Variables de Entorno por Servicio (del código fuente)

### api-gateway (`apps/api-gateway/internal/config/config.go`)
```
PORT=8080
ENVIRONMENT=production
CORE_SERVICE_URL=<cloud-run-core-url>
AI_SERVICE_URL=<cloud-run-ai-url>
NOTIFICATION_SERVICE_URL=<cloud-run-notification-url>
FIREBASE_PROJECT_ID=<secret>
FIREBASE_CREDENTIALS=<secret>   # path o JSON
RATE_LIMIT_RPS=100
CORS_ORIGINS=https://<domain>
```

### core-service (`apps/core-service/src/config.py`)
```
PORT=8081
ENV=production
DEBUG=false
DATABASE_URL=<secret>           # postgresql+asyncpg://...
FIREBASE_PROJECT_ID=<secret>
FIREBASE_CREDENTIALS_PATH=<secret>
SECRET_KEY=<secret>
CORS_ORIGINS=https://<domain>
```

### ai-service (`apps/ai-service/src/config.py`)
```
PORT=8082
environment=production
DATABASE_URL=<secret>
gcp_project_id=projectforge-4314f
gcp_location=us-central1
gcs_bucket_name=projectforge-documents
vertex_embedding_model=text-embedding-004
vertex_llm_model=gemini-2.0-flash
```

### notification-service (`apps/notification-service` config)
```
PORT=8083
RESEND_API_KEY=<secret>
SLACK_BOT_TOKEN=<secret>
```

## Estructura de Archivos a Crear

```
infrastructure/terraform/
├── backend.tf                          # GCS remote state
├── versions.tf                         # Provider versions
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cloud-sql/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cloud-run/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cloud-storage/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── load-balancer/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── secret-manager/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── iam/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev/
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── terraform.tfvars
    ├── staging/
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── terraform.tfvars
    └── prod/
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars
```

## Especificación de Módulos

---

### backend.tf (raíz de terraform/)

El estado remoto debe vivir en GCS. **Este bucket debe crearse manualmente ANTES de correr Terraform por primera vez** (no puede auto-crearse).

```hcl
terraform {
  backend "gcs" {
    bucket = "projectforge-terraform-state"
    prefix = "terraform/state"
  }
}
```

Nota en `README` del directorio: crear el bucket con `gsutil mb gs://projectforge-terraform-state`

---

### versions.tf (raíz de terraform/)

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}
```

---

### módulo: vpc/

**Recursos**:
- `google_compute_network` — VPC dedicada (no default), `auto_create_subnetworks = false`
- `google_compute_subnetwork` — subnet privada en `us-central1` con CIDR `10.0.0.0/24`
- `google_compute_router` — para Cloud NAT
- `google_compute_router_nat` — NAT para tráfico egress de Cloud Run
- `google_vpc_access_connector` — Serverless VPC Connector para Cloud Run → Cloud SQL
  - CIDR: `10.8.0.0/28`
  - `min_instances = 2`, `max_instances = 3`
  - `machine_type = "f1-micro"` (dev) / `"e2-standard-4"` (prod)
- `google_compute_global_address` — rango de IP para Private Service Connect (Cloud SQL private IP)
- `google_service_networking_connection` — peering con `servicenetworking.googleapis.com`

**Variables**: `project_id`, `region`, `environment`, `vpc_cidr`
**Outputs**: `vpc_id`, `vpc_name`, `subnet_id`, `vpc_connector_id`, `vpc_connector_name`

---

### módulo: iam/

Crear un `google_service_account` por servicio con el principio de menor privilegio:

| Service Account | Roles |
|----------------|-------|
| `sa-api-gateway` | `roles/run.invoker` (para llamar a otros Cloud Run) |
| `sa-core-service` | `roles/cloudsql.client`, `roles/secretmanager.secretAccessor` |
| `sa-ai-service` | `roles/cloudsql.client`, `roles/secretmanager.secretAccessor`, `roles/storage.objectAdmin`, `roles/aiplatform.user` |
| `sa-notification-service` | `roles/secretmanager.secretAccessor` |
| `sa-cloud-build` | `roles/run.admin`, `roles/storage.admin`, `roles/iam.serviceAccountUser`, `roles/artifactregistry.writer` |

```hcl
resource "google_service_account" "api_gateway" {
  account_id   = "sa-api-gateway-${var.environment}"
  display_name = "API Gateway Service Account (${var.environment})"
  project      = var.project_id
}
```

**Outputs**: todas las SAs como `email` para usarlas en Cloud Run y Secret Manager

---

### módulo: secret-manager/

Crear secretos para cada valor sensible. Los valores de los secretos se pasan como variables sensibles — **Terraform NO guarda secretos en estado, solo crea el recurso y la versión inicial**.

Secretos a crear:
- `database-url` — `postgresql+asyncpg://app:password@CLOUD_SQL_IP/projectforge`
- `firebase-project-id` — ID del proyecto Firebase
- `firebase-credentials` — JSON del service account de Firebase (base64 o raw JSON)
- `secret-key` — clave aleatoria para core-service (`random_password`)
- `resend-api-key`
- `slack-bot-token`
- `cloud-sql-password` — contraseña del usuario PostgreSQL app

Para cada secreto, crear un `google_secret_manager_secret_iam_binding` por service account que lo necesite.

```hcl
resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = var.database_url  # sensitive variable
}

resource "google_secret_manager_secret_iam_member" "database_url_core" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.core_service_sa_email}"
}
```

**Outputs**: ARN/nombre completo de cada secreto para referenciarlo en Cloud Run

---

### módulo: cloud-sql/

```hcl
resource "google_sql_database_instance" "main" {
  name             = "projectforge-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  deletion_protection = var.environment == "prod" ? true : false

  settings {
    tier = var.db_tier  # "db-f1-micro" dev, "db-custom-2-4096" prod

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "prod" ? true : false
      transaction_log_retention_days = var.environment == "prod" ? 7 : 1
      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 14 : 3
      }
    }

    ip_configuration {
      ipv4_enabled    = false  # Sin IP pública
      private_network = var.vpc_id
      enable_private_path_for_google_cloud_services = true
    }

    database_flags {
      name  = "max_connections"
      value = var.environment == "prod" ? "200" : "50"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
    }
  }
}

resource "google_sql_database" "projectforge" {
  name     = "projectforge"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

resource "google_sql_user" "app" {
  name     = "app"
  instance = google_sql_database_instance.main.name
  password = var.db_password  # viene de secret-manager
  project  = var.project_id
}
```

**Nota sobre pgvector**: La extensión `vector` se instala via migración SQL (`CREATE EXTENSION IF NOT EXISTS vector`), no via Terraform. Cloud SQL para PostgreSQL 15 la soporta nativamente desde 2023.

**Variables**: `project_id`, `region`, `environment`, `vpc_id`, `db_tier`, `db_password`
**Outputs**: `instance_name`, `instance_connection_name`, `private_ip_address`, `database_name`

---

### módulo: cloud-storage/

**Bucket 1: Documentos**
```hcl
resource "google_storage_bucket" "documents" {
  name          = "projectforge-documents-${var.environment}"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["Content-Type", "Authorization"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition { age = 365 }
    action    { type = "SetStorageClass"; storage_class = "NEARLINE" }
  }
}
```

**Bucket 2: Frontend estático**
```hcl
resource "google_storage_bucket" "frontend" {
  name          = "projectforge-frontend-${var.environment}"
  location      = "US"  # Multi-regional para CDN
  force_destroy = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"  # SPA routing
  }

  uniform_bucket_level_access = false  # Necesario para ACLs públicas
}

resource "google_storage_bucket_iam_member" "frontend_public" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
```

**Outputs**: `documents_bucket_name`, `frontend_bucket_name`, `frontend_bucket_url`

---

### módulo: cloud-run/

Módulo reutilizable para cualquier servicio Cloud Run:

```hcl
resource "google_cloud_run_v2_service" "service" {
  name     = var.name
  location = var.region
  project  = var.project_id

  ingress = var.allow_public ? "INGRESS_TRAFFIC_ALL" : "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = var.service_account_email

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image

      ports {
        container_port = var.port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle          = var.min_instances == 0  # CPU throttle cuando idle si escala a 0
        startup_cpu_boost = true
      }

      # Variables de entorno planas
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Variables de entorno desde Secret Manager
      dynamic "env" {
        for_each = var.secret_env_vars
        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = "latest"
            }
          }
        }
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        period_seconds        = 30
        failure_threshold     = 3
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 10
      }
    }
  }
}

# IAM para hacer el servicio invocable
resource "google_cloud_run_v2_service_iam_member" "invoker" {
  count    = var.allow_public ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

**Variables**: `project_id`, `region`, `name`, `image`, `port`, `cpu`, `memory`, `min_instances`, `max_instances`, `service_account_email`, `vpc_connector_id`, `allow_public`, `env_vars` (map), `secret_env_vars` (list of objects)
**Outputs**: `service_url`, `service_name`, `latest_revision`

---

### módulo: load-balancer/

Componentes:
1. **IP estática global**: `google_compute_global_address`
2. **Certificado SSL gestionado**: `google_compute_managed_ssl_certificate`
3. **NEG serverless** para api-gateway: `google_compute_region_network_endpoint_group` con `cloud_run { service = var.api_gateway_service_name }`
4. **Backend para API** (Cloud Run): `google_compute_backend_service` apuntando al NEG
5. **Backend para frontend** (Cloud Storage): `google_compute_backend_bucket` con CDN habilitado
6. **URL Map**: `/api/*` → api-gateway backend, `/*` → frontend backend
7. **HTTPS Proxy**: `google_compute_target_https_proxy` referenciando el URL Map y el certificado SSL
8. **HTTP→HTTPS redirect**: `google_compute_url_map` separado + `google_compute_target_http_proxy`
9. **Forwarding rules**: puerto 443 (HTTPS) y puerto 80 (HTTP→redirect)

**Cloud Armor (WAF)**:
```hcl
resource "google_compute_security_policy" "waf" {
  name    = "projectforge-waf-${var.environment}"
  project = var.project_id

  # Regla: bloquear IPs con demasiados requests (rate limiting)
  rule {
    action   = "throttle"
    priority = 1000
    match {
      versioned_expr = "SRC_IPS_V1"
      config { src_ip_ranges = ["*"] }
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
  }

  # Regla: bloquear OWASP Top 10
  rule {
    action   = "deny(403)"
    priority = 2000
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-stable')"
      }
    }
  }

  rule {
    action   = "deny(403)"
    priority = 2001
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-stable')"
      }
    }
  }

  # Regla default: allow all
  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config { src_ip_ranges = ["*"] }
    }
  }
}
```

Asociar la security policy al `google_compute_backend_service` del api-gateway.

**Variables**: `project_id`, `region`, `domain_name`, `api_gateway_service_name`, `frontend_bucket_name`
**Outputs**: `load_balancer_ip`, `https_url`

---

## Environments (dev / staging / prod)

Cada ambiente tiene su propio directorio con `main.tf` que llama a todos los módulos con los valores apropiados.

### environments/dev/terraform.tfvars

```hcl
project_id         = "projectforge-4314f"
region             = "us-central1"
environment        = "dev"
domain_name        = "dev.projectforge.app"
firebase_project_id = "projectforge-4314f"

# Cloud SQL
db_tier = "db-f1-micro"

# Cloud Run - recursos mínimos para dev
api_gateway_cpu     = "1"
api_gateway_memory  = "512Mi"
api_gateway_min     = 1
api_gateway_max     = 3

core_service_cpu    = "1"
core_service_memory = "1Gi"
core_service_min    = 1
core_service_max    = 3

ai_service_cpu      = "2"
ai_service_memory   = "2Gi"
ai_service_min      = 0   # escala a 0 en dev
ai_service_max      = 2

notification_cpu    = "0.5"
notification_memory = "256Mi"
notification_min    = 0   # escala a 0 en dev
notification_max    = 2
```

### environments/prod/terraform.tfvars

```hcl
project_id         = "projectforge-4314f"
region             = "us-central1"
environment        = "prod"
domain_name        = "app.projectforge.app"
firebase_project_id = "projectforge-4314f"

# Cloud SQL
db_tier = "db-custom-2-4096"

# Cloud Run - producción
api_gateway_cpu     = "2"
api_gateway_memory  = "1Gi"
api_gateway_min     = 2
api_gateway_max     = 10

core_service_cpu    = "2"
core_service_memory = "2Gi"
core_service_min    = 2
core_service_max    = 10

ai_service_cpu      = "4"
ai_service_memory   = "4Gi"
ai_service_min      = 1
ai_service_max      = 5

notification_cpu    = "1"
notification_memory = "512Mi"
notification_min    = 1
notification_max    = 3
```

---

## environments/dev/main.tf — Estructura Completa

```hcl
locals {
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

# APIs necesarias
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "aiplatform.googleapis.com",
    "documentai.googleapis.com",
    "pubsub.googleapis.com",
    "cloudtasks.googleapis.com",
    "firestore.googleapis.com",
  ])
  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

# Artifact Registry para imágenes Docker
resource "google_artifact_registry_repository" "docker" {
  location      = local.region
  repository_id = "projectforge"
  format        = "DOCKER"
  project       = local.project_id
}

module "iam" {
  source      = "../../modules/iam"
  project_id  = local.project_id
  environment = local.environment
}

module "vpc" {
  source      = "../../modules/vpc"
  project_id  = local.project_id
  region      = local.region
  environment = local.environment
  depends_on  = [google_project_service.apis]
}

module "secrets" {
  source                    = "../../modules/secret-manager"
  project_id                = local.project_id
  environment               = local.environment
  core_service_sa_email     = module.iam.core_service_sa_email
  ai_service_sa_email       = module.iam.ai_service_sa_email
  notification_service_sa_email = module.iam.notification_service_sa_email
  # Valores sensibles: pasar via TF_VAR_* o terraform.tfvars (NO commitear)
  database_url              = var.database_url
  firebase_project_id       = var.firebase_project_id
  firebase_credentials      = var.firebase_credentials
  resend_api_key            = var.resend_api_key
  slack_bot_token           = var.slack_bot_token
  db_password               = var.db_password
}

module "cloud_sql" {
  source      = "../../modules/cloud-sql"
  project_id  = local.project_id
  region      = local.region
  environment = local.environment
  vpc_id      = module.vpc.vpc_id
  db_tier     = var.db_tier
  db_password = var.db_password
  depends_on  = [module.vpc]
}

module "storage" {
  source       = "../../modules/cloud-storage"
  project_id   = local.project_id
  region       = local.region
  environment  = local.environment
  cors_origins = ["https://${var.domain_name}"]
}

# Cloud Run Services
module "api_gateway" {
  source                = "../../modules/cloud-run"
  project_id            = local.project_id
  region                = local.region
  name                  = "api-gateway-${local.environment}"
  image                 = "${local.region}-docker.pkg.dev/${local.project_id}/projectforge/api-gateway:latest"
  port                  = 8080
  cpu                   = var.api_gateway_cpu
  memory                = var.api_gateway_memory
  min_instances         = var.api_gateway_min
  max_instances         = var.api_gateway_max
  service_account_email = module.iam.api_gateway_sa_email
  vpc_connector_id      = module.vpc.vpc_connector_id
  allow_public          = false  # Solo accesible via Load Balancer
  env_vars = {
    ENVIRONMENT             = local.environment
    PORT                    = "8080"
    CORE_SERVICE_URL        = module.core_service.service_url
    AI_SERVICE_URL          = module.ai_service.service_url
    NOTIFICATION_SERVICE_URL = module.notification_service.service_url
    CORS_ORIGINS            = "https://${var.domain_name}"
    RATE_LIMIT_RPS          = "100"
  }
  secret_env_vars = [
    { name = "FIREBASE_PROJECT_ID", secret = module.secrets.firebase_project_id_secret_id },
    { name = "FIREBASE_CREDENTIALS", secret = module.secrets.firebase_credentials_secret_id },
  ]
  depends_on = [module.vpc, module.secrets]
}

module "core_service" {
  source                = "../../modules/cloud-run"
  project_id            = local.project_id
  region                = local.region
  name                  = "core-service-${local.environment}"
  image                 = "${local.region}-docker.pkg.dev/${local.project_id}/projectforge/core-service:latest"
  port                  = 8081
  cpu                   = var.core_service_cpu
  memory                = var.core_service_memory
  min_instances         = var.core_service_min
  max_instances         = var.core_service_max
  service_account_email = module.iam.core_service_sa_email
  vpc_connector_id      = module.vpc.vpc_connector_id
  allow_public          = false
  env_vars = {
    PORT        = "8081"
    ENV         = local.environment
    DEBUG       = "false"
    CORS_ORIGINS = "https://${var.domain_name}"
    FIREBASE_PROJECT_ID = var.firebase_project_id
  }
  secret_env_vars = [
    { name = "DATABASE_URL", secret = module.secrets.database_url_secret_id },
    { name = "SECRET_KEY",   secret = module.secrets.secret_key_secret_id },
    { name = "FIREBASE_CREDENTIALS_PATH", secret = module.secrets.firebase_credentials_secret_id },
  ]
  depends_on = [module.cloud_sql, module.secrets]
}

module "ai_service" {
  source                = "../../modules/cloud-run"
  project_id            = local.project_id
  region                = local.region
  name                  = "ai-service-${local.environment}"
  image                 = "${local.region}-docker.pkg.dev/${local.project_id}/projectforge/ai-service:latest"
  port                  = 8082
  cpu                   = var.ai_service_cpu
  memory                = var.ai_service_memory
  min_instances         = var.ai_service_min
  max_instances         = var.ai_service_max
  service_account_email = module.iam.ai_service_sa_email
  vpc_connector_id      = module.vpc.vpc_connector_id
  allow_public          = false
  env_vars = {
    PORT                    = "8082"
    environment             = local.environment
    gcp_project_id          = local.project_id
    gcp_location            = local.region
    gcs_bucket_name         = module.storage.documents_bucket_name
    vertex_embedding_model  = "text-embedding-004"
    vertex_llm_model        = "gemini-2.0-flash"
  }
  secret_env_vars = [
    { name = "DATABASE_URL", secret = module.secrets.database_url_secret_id },
  ]
  depends_on = [module.cloud_sql, module.secrets, module.storage]
}

module "notification_service" {
  source                = "../../modules/cloud-run"
  project_id            = local.project_id
  region                = local.region
  name                  = "notification-service-${local.environment}"
  image                 = "${local.region}-docker.pkg.dev/${local.project_id}/projectforge/notification-service:latest"
  port                  = 8083
  cpu                   = var.notification_cpu
  memory                = var.notification_memory
  min_instances         = var.notification_min
  max_instances         = var.notification_max
  service_account_email = module.iam.notification_service_sa_email
  vpc_connector_id      = module.vpc.vpc_connector_id
  allow_public          = false
  env_vars = {
    PORT        = "8083"
    ENVIRONMENT = local.environment
  }
  secret_env_vars = [
    { name = "RESEND_API_KEY",   secret = module.secrets.resend_api_key_secret_id },
    { name = "SLACK_BOT_TOKEN",  secret = module.secrets.slack_bot_token_secret_id },
  ]
  depends_on = [module.secrets]
}

module "load_balancer" {
  source                   = "../../modules/load-balancer"
  project_id               = local.project_id
  region                   = local.region
  environment              = local.environment
  domain_name              = var.domain_name
  api_gateway_service_name = module.api_gateway.service_name
  frontend_bucket_name     = module.storage.frontend_bucket_name
  depends_on               = [module.api_gateway, module.storage]
}
```

---

## Consideraciones Críticas de Implementación

### 1. Cloud Run → Cloud SQL (conexión privada)
Cloud Run requiere el Serverless VPC Connector para acceder a Cloud SQL por IP privada. La variable `egress = "PRIVATE_RANGES_ONLY"` asegura que solo el tráfico a rangos privados pase por el VPC Connector. La URL de conexión en Database es la IP privada de Cloud SQL, **no** el Cloud SQL Auth Proxy URL (que sería el formato `postgres://user:pass@/db?host=/cloudsql/...`).

### 2. AI Service — Service Account y Vertex AI
El service account `sa-ai-service` necesita `roles/aiplatform.user` para llamar a Vertex AI. Vertex AI usa Application Default Credentials automáticamente cuando el servicio corre en GCP con el service account correcto — no se necesita clave JSON.

### 3. Secretos sensibles nunca en tfvars commiteados
Los valores de secretos (passwords, API keys) se deben pasar como variables de Terraform usando variables de entorno `TF_VAR_*` o un archivo `secrets.tfvars` que **debe estar en `.gitignore`**. Añadir `secrets.tfvars` al `.gitignore` existente.

### 4. Imagen Docker inicial
La primera vez que se aplique Terraform, las imágenes Docker deben existir en Artifact Registry. El flujo es:
```bash
# 1. Crear infra (incluye Artifact Registry)
terraform apply -target=google_artifact_registry_repository.docker

# 2. Build y push imágenes
gcloud builds submit apps/api-gateway --tag us-central1-docker.pkg.dev/projectforge-4314f/projectforge/api-gateway:latest

# 3. Aplicar el resto
terraform apply
```

### 5. Bootstrap del bucket de estado
Antes de cualquier `terraform init`:
```bash
gsutil mb -p projectforge-4314f -l us-central1 gs://projectforge-terraform-state
gsutil versioning set on gs://projectforge-terraform-state
```

### 6. Cloud SQL private IP y VPC peering
El peering con `servicenetworking.googleapis.com` puede tardar varios minutos. Usar `depends_on` entre el módulo VPC y cloud-sql. El recurso `google_service_networking_connection` puede requerir el flag `terraform apply -parallelism=1` la primera vez.

### 7. Frontend SPA y not_found_page
El bucket de frontend tiene `not_found_page = "index.html"` para que React Router funcione correctamente (todas las rutas sirven el mismo `index.html`). El Load Balancer debe configurar el backend bucket con `google_compute_backend_bucket` (no `backend_service`).

### 8. IAM binding para inter-service calls
Los servicios Cloud Run que llaman a otros Cloud Run deben tener el rol `roles/run.invoker`. El api-gateway necesita este rol en todos los servicios downstream. Configurar en el módulo IAM o como output de cada Cloud Run para el binding.

## Checklist de Entrega

- [ ] `backend.tf` y `versions.tf` en raíz de `infrastructure/terraform/`
- [ ] Módulo `vpc/` con VPC, subnet, NAT, Serverless VPC Connector
- [ ] Módulo `iam/` con 5 service accounts y sus roles mínimos
- [ ] Módulo `secret-manager/` con 7 secretos y IAM bindings por SA
- [ ] Módulo `cloud-sql/` con PostgreSQL 15, Private IP, backups, sin IP pública
- [ ] Módulo `cloud-storage/` con bucket de documentos y bucket de frontend (SPA-ready)
- [ ] Módulo `cloud-run/` reutilizable con health probes, scaling, VPC, secret env vars
- [ ] Módulo `load-balancer/` con IP estática, SSL, URL Map, CDN, Cloud Armor WAF
- [ ] Environments `dev/`, `staging/`, `prod/` con `main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars`
- [ ] `secrets.tfvars` añadido al `.gitignore` del proyecto
- [ ] `README.md` en `infrastructure/terraform/` con instrucciones de bootstrap y orden de operaciones
- [ ] `terraform validate` sin errores en todos los environments
- [ ] `terraform fmt -recursive` aplicado
