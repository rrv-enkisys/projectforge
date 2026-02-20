# CI/CD GitHub Actions Agent

You are a DevOps specialist for ProjectForge. Your sole responsibility is to create three GitHub Actions workflow files. The `.github/` directory does **not exist** yet — créalo desde cero.

## Estructura a Crear

```
.github/
└── workflows/
    ├── ci.yml           # PR to main → lint + test + build check
    ├── deploy-dev.yml   # Push to main → build + push + deploy dev
    └── deploy-prod.yml  # Release published → staging + approval + prod
```

## Estado del Proyecto (del código fuente)

### Lenguajes y versiones confirmadas

| Componente | Versión | Fuente |
|-----------|---------|--------|
| Go (api-gateway) | **1.23** | `apps/api-gateway/go.mod`: `go 1.23.0` |
| Go (notification-service) | **1.22** | `apps/notification-service/go.mod`: `go 1.22` |
| Python (ambos servicios) | **3.12** | `pyproject.toml`: `target-version = "py312"` |
| Poetry | **1.7.1** | `apps/core-service/Dockerfile` + `apps/ai-service/Dockerfile` |
| Node | **20** | `apps/web/Dockerfile`: `FROM node:20-alpine` |
| pnpm | workspace | `pnpm-workspace.yaml`, `package.json` |

### Comandos de lint confirmados (del Makefile)

```bash
# Python (core-service y ai-service)
cd apps/core-service && black . && isort . && mypy . && ruff check .

# Go
cd apps/api-gateway && gofmt -w .
cd apps/notification-service && gofmt -w .

# Frontend
pnpm lint   # → turbo lint → apps/web: eslint
```

### Comandos de test confirmados

```bash
# Python core-service (necesita PostgreSQL en localhost:5432)
cd apps/core-service && pytest -v --cov=src tests/

# Python ai-service (NO necesita GCP - usa mocks en conftest.py)
cd apps/ai-service && pytest -v --cov=src tests/

# Go api-gateway (unit tests en internal/middleware/ y internal/handler/)
cd apps/api-gateway && go test -v ./...

# Go notification-service (unit tests en internal/service/)
cd apps/notification-service && go test -v ./...
```

### Tests de Python - Detalles críticos

**core-service/tests/conftest.py**:
- Usa `TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge_test"`
- Requiere PostgreSQL con pgvector — usar `ankane/pgvector` imagen en services
- `asyncio_mode = "auto"` ya está en `pyproject.toml` — no agregar flag en CLI
- Tests crean y dropean tablas (scope="session") — **NO** ejecutar en la DB de producción

**ai-service/tests/conftest.py**:
- Tiene `mock_vertex_client` que mockea todas las llamadas a Vertex AI
- **NO necesita** `GCP_SA_KEY` para los tests
- Puede correr sin ninguna credencial GCP

### Frontend

- **No hay archivos de test (`*.test.tsx`) aún** — el job de test frontend debe ser condicional
- El build (`pnpm build`) sí existe y compila TypeScript + Vite
- El lint (`pnpm lint`) ejecuta ESLint en `apps/web/src/`

### Docker images (confirmados por Dockerfiles)

| Servicio | Dockerfile build binary | Puerto |
|---------|------------------------|--------|
| api-gateway | `./cmd/server` → `gateway` | 8080 |
| core-service | Python/uvicorn | 8081 |
| ai-service | Python/uvicorn | 8082 |
| notification-service | `.` → `main` | 8083 |

### Artifact Registry

```
Region: us-central1
Repositorio: projectforge
Proyecto: projectforge-4314f

URLs de imágenes:
us-central1-docker.pkg.dev/projectforge-4314f/projectforge/api-gateway
us-central1-docker.pkg.dev/projectforge-4314f/projectforge/core-service
us-central1-docker.pkg.dev/projectforge-4314f/projectforge/ai-service
us-central1-docker.pkg.dev/projectforge-4314f/projectforge/notification-service
```

## Secrets Requeridos en GitHub

Configurar en Settings → Secrets and variables → Actions:

| Secret | Descripción |
|--------|-------------|
| `GCP_PROJECT_ID` | `projectforge-4314f` |
| `GCP_SA_KEY` | JSON del Service Account con roles: `roles/run.admin`, `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser`, `roles/storage.admin` |
| `FIREBASE_PROJECT_ID` | Firebase project ID |
| `RESEND_API_KEY` | Para notification-service en dev |
| `SLACK_BOT_TOKEN` | Para notification-service en dev |

> **Recomendación de seguridad**: Workload Identity Federation elimina la necesidad de `GCP_SA_KEY` (no hay claves JSON de larga duración). Documentar en comentario del workflow pero implementar con SA Key para simplicidad inicial.

## Workflow 1: ci.yml

**Trigger**: `pull_request` targeting `main`
**Objetivo**: Rápido, paralelo, sin deploys

```yaml
name: CI

on:
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # ─── FRONTEND ────────────────────────────────────────────────────
  lint-frontend:
    name: Lint Frontend
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/web
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 8   # versión compatible con pnpm-lock.yaml

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile
        working-directory: .   # instalar desde raíz del monorepo

      - name: Lint
        run: pnpm --filter @projectforge/web lint

      - name: Type check (tsc)
        run: pnpm --filter @projectforge/web exec tsc --noEmit

  build-frontend:
    name: Build Frontend
    runs-on: ubuntu-latest
    needs: lint-frontend
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 8

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Build
        run: pnpm --filter @projectforge/web build
        env:
          VITE_API_URL: http://localhost:8080   # placeholder para build check

  # ─── PYTHON SERVICES ─────────────────────────────────────────────
  lint-core-service:
    name: Lint Core Service
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/core-service
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Poetry
        run: pip install poetry==1.7.1

      - name: Cache Poetry deps
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: poetry-core-${{ hashFiles('apps/core-service/poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: ruff check
        run: poetry run ruff check .

      - name: black --check
        run: poetry run black --check .

      - name: isort --check
        run: poetry run isort --check-only .

      - name: mypy
        run: poetry run mypy src/
        env:
          FIREBASE_PROJECT_ID: test-project   # mypy no hace llamadas reales

  lint-ai-service:
    name: Lint AI Service
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/ai-service
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Poetry
        run: pip install poetry==1.7.1

      - name: Cache Poetry deps
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: poetry-ai-${{ hashFiles('apps/ai-service/poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: ruff check
        run: poetry run ruff check .

      - name: black --check
        run: poetry run black --check .

      - name: isort --check
        run: poetry run isort --check-only .

      - name: mypy
        run: poetry run mypy src/

  test-core-service:
    name: Test Core Service
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/core-service
    services:
      postgres:
        image: ankane/pgvector:v0.7.0   # PostgreSQL 15 + pgvector
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: projectforge_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Poetry
        run: pip install poetry==1.7.1

      - name: Cache Poetry deps
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: poetry-core-${{ hashFiles('apps/core-service/poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Run migrations on test DB
        run: |
          poetry run python -c "
          import asyncio
          from sqlalchemy.ext.asyncio import create_async_engine
          from src.database import Base
          async def create_tables():
              engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge_test')
              async with engine.begin() as conn:
                  await conn.run_sync(Base.metadata.create_all)
              await engine.dispose()
          asyncio.run(create_tables())
          "
        env:
          FIREBASE_PROJECT_ID: test-project

      - name: Run tests
        run: poetry run pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing
        env:
          FIREBASE_PROJECT_ID: test-project
          DEBUG: "true"

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: core-service-coverage
          path: apps/core-service/coverage.xml

  test-ai-service:
    name: Test AI Service
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/ai-service
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Poetry
        run: pip install poetry==1.7.1

      - name: Cache Poetry deps
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: poetry-ai-${{ hashFiles('apps/ai-service/poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Run unit tests only (sin integración - no requieren DB)
        run: poetry run pytest tests/unit/ -v --cov=src --cov-report=xml
        # Los tests de integración de AI service necesitan DB — separar en otro job si se necesita

  # ─── GO SERVICES ─────────────────────────────────────────────────
  test-api-gateway:
    name: Test API Gateway
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/api-gateway
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
          cache-dependency-path: apps/api-gateway/go.sum

      - name: Download modules
        run: go mod download

      - name: Run tests
        run: go test -v -race -coverprofile=coverage.out ./...

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: gateway-coverage
          path: apps/api-gateway/coverage.out

  test-notification-service:
    name: Test Notification Service
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/notification-service
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'   # usar 1.23 que es compatible con 1.22
          cache-dependency-path: apps/notification-service/go.sum

      - name: Download modules
        run: go mod download

      - name: Run tests
        run: go test -v -race ./...

  # ─── DOCKER BUILD CHECK ──────────────────────────────────────────
  build-images:
    name: Build Docker Images (no push)
    runs-on: ubuntu-latest
    needs:
      - lint-frontend
      - lint-core-service
      - lint-ai-service
      - test-api-gateway
      - test-notification-service
    strategy:
      matrix:
        service:
          - name: api-gateway
            context: apps/api-gateway
          - name: core-service
            context: apps/core-service
          - name: ai-service
            context: apps/ai-service
          - name: notification-service
            context: apps/notification-service
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - name: Build ${{ matrix.service.name }}
        uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.service.context }}
          push: false
          tags: projectforge/${{ matrix.service.name }}:pr-${{ github.event.pull_request.number }}
          cache-from: type=gha,scope=${{ matrix.service.name }}
          cache-to: type=gha,mode=max,scope=${{ matrix.service.name }}
```

## Workflow 2: deploy-dev.yml

**Trigger**: `push` to `main`
**Objetivo**: Build todas las imágenes, push a Artifact Registry, deploy a Cloud Run dev

```yaml
name: Deploy to Dev

on:
  push:
    branches: [main]

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  REGISTRY: us-central1-docker.pkg.dev
  REPOSITORY: projectforge
  IMAGE_TAG: ${{ github.sha }}

jobs:
  build-and-push:
    name: Build & Push Images
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write   # para Workload Identity (futuro)
    outputs:
      image_tag: ${{ env.IMAGE_TAG }}
    strategy:
      matrix:
        service:
          - name: api-gateway
            context: apps/api-gateway
          - name: core-service
            context: apps/core-service
          - name: ai-service
            context: apps/ai-service
          - name: notification-service
            context: apps/notification-service
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      - uses: docker/setup-buildx-action@v3

      - name: Build and push ${{ matrix.service.name }}
        uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.service.context }}
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ matrix.service.name }}:${{ env.IMAGE_TAG }}
            ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ matrix.service.name }}:latest
          cache-from: type=gha,scope=${{ matrix.service.name }}
          cache-to: type=gha,mode=max,scope=${{ matrix.service.name }}
          labels: |
            org.opencontainers.image.revision=${{ github.sha }}
            org.opencontainers.image.source=${{ github.repository }}

  deploy-dev:
    name: Deploy to Dev
    runs-on: ubuntu-latest
    needs: build-and-push
    environment:
      name: dev
      url: https://dev.projectforge.app
    strategy:
      max-parallel: 1   # deploy secuencial para evitar race conditions en Cloud Run
      matrix:
        service:
          - name: api-gateway
            cloud_run_name: api-gateway-dev
          - name: core-service
            cloud_run_name: core-service-dev
          - name: ai-service
            cloud_run_name: ai-service-dev
          - name: notification-service
            cloud_run_name: notification-service-dev
    steps:
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Deploy ${{ matrix.service.name }} to Cloud Run
        run: |
          gcloud run deploy ${{ matrix.service.cloud_run_name }} \
            --image ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ matrix.service.name }}:${{ env.IMAGE_TAG }} \
            --region ${{ env.REGION }} \
            --project ${{ env.PROJECT_ID }} \
            --platform managed \
            --quiet

      - name: Verify deployment health
        run: |
          SERVICE_URL=$(gcloud run services describe ${{ matrix.service.cloud_run_name }} \
            --region ${{ env.REGION }} \
            --project ${{ env.PROJECT_ID }} \
            --format 'value(status.url)')
          echo "Service URL: $SERVICE_URL"
          # Health check con retry
          for i in {1..5}; do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" || echo "000")
            if [ "$STATUS" = "200" ]; then
              echo "✓ Health check passed"
              break
            fi
            echo "Attempt $i: status $STATUS, retrying in 10s..."
            sleep 10
          done
          if [ "$STATUS" != "200" ]; then
            echo "✗ Health check failed after 5 attempts"
            exit 1
          fi

  notify-dev-deploy:
    name: Notify Dev Deploy
    runs-on: ubuntu-latest
    needs: deploy-dev
    if: always()
    steps:
      - name: Slack notification
        uses: slackapi/slack-github-action@v1.26.0
        if: ${{ secrets.SLACK_BOT_TOKEN != '' }}
        with:
          payload: |
            {
              "text": "${{ needs.deploy-dev.result == 'success' && '✅' || '❌' }} Dev deploy ${{ needs.deploy-dev.result }}: ${{ github.repository }}@${{ github.sha }}",
              "attachments": [{
                "color": "${{ needs.deploy-dev.result == 'success' && 'good' || 'danger' }}",
                "fields": [
                  {"title": "Branch", "value": "${{ github.ref_name }}", "short": true},
                  {"title": "Commit", "value": "${{ github.sha }}", "short": true}
                ]
              }]
            }
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

## Workflow 3: deploy-prod.yml

**Trigger**: `release` published (tag `v*.*.*`)
**Objetivo**: Build + push → staging → smoke tests → **manual approval** → prod

```yaml
name: Deploy to Production

on:
  release:
    types: [published]

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  REGISTRY: us-central1-docker.pkg.dev
  REPOSITORY: projectforge
  IMAGE_TAG: ${{ github.event.release.tag_name }}

jobs:
  build-and-push-release:
    name: Build & Push Release Images
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
          - name: api-gateway
            context: apps/api-gateway
          - name: core-service
            context: apps/core-service
          - name: ai-service
            context: apps/ai-service
          - name: notification-service
            context: apps/notification-service
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.release.tag_name }}

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      - uses: docker/setup-buildx-action@v3

      - name: Build and push ${{ matrix.service.name }}
        uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.service.context }}
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ matrix.service.name }}:${{ env.IMAGE_TAG }}
            ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ matrix.service.name }}:stable
          cache-from: type=gha,scope=${{ matrix.service.name }}
          cache-to: type=gha,mode=max,scope=${{ matrix.service.name }}
          labels: |
            org.opencontainers.image.version=${{ env.IMAGE_TAG }}
            org.opencontainers.image.revision=${{ github.sha }}

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build-and-push-release
    environment:
      name: staging
      url: https://staging.projectforge.app
    strategy:
      max-parallel: 1
      matrix:
        service:
          - name: api-gateway
            cloud_run_name: api-gateway-staging
          - name: core-service
            cloud_run_name: core-service-staging
          - name: ai-service
            cloud_run_name: ai-service-staging
          - name: notification-service
            cloud_run_name: notification-service-staging
    steps:
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Deploy ${{ matrix.service.name }} to Staging
        run: |
          gcloud run deploy ${{ matrix.service.cloud_run_name }} \
            --image ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ matrix.service.name }}:${{ env.IMAGE_TAG }} \
            --region ${{ env.REGION }} \
            --project ${{ env.PROJECT_ID }} \
            --platform managed \
            --quiet

  smoke-tests:
    name: Smoke Tests (Staging)
    runs-on: ubuntu-latest
    needs: deploy-staging
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Get staging URLs
        id: urls
        run: |
          GATEWAY_URL=$(gcloud run services describe api-gateway-staging \
            --region ${{ env.REGION }} --project ${{ env.PROJECT_ID }} \
            --format 'value(status.url)')
          echo "gateway_url=$GATEWAY_URL" >> $GITHUB_OUTPUT

      - name: Health checks
        run: |
          BASE_URL="${{ steps.urls.outputs.gateway_url }}"
          echo "Testing: $BASE_URL"

          check() {
            local endpoint=$1
            local expected=$2
            local status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
            if [ "$status" = "$expected" ]; then
              echo "✓ $endpoint → $status"
            else
              echo "✗ $endpoint → $status (expected $expected)"
              exit 1
            fi
          }

          check "/health" "200"
          # API routes requieren auth → esperamos 401
          check "/api/v1/projects" "401"
          check "/api/v1/tasks" "401"

      - name: Core Service direct health check
        run: |
          CORE_URL=$(gcloud run services describe core-service-staging \
            --region ${{ env.REGION }} --project ${{ env.PROJECT_ID }} \
            --format 'value(status.url)')
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CORE_URL/health")
          [ "$STATUS" = "200" ] && echo "✓ Core Service healthy" || (echo "✗ Core Service unhealthy: $STATUS" && exit 1)

      - name: AI Service direct health check
        run: |
          AI_URL=$(gcloud run services describe ai-service-staging \
            --region ${{ env.REGION }} --project ${{ env.PROJECT_ID }} \
            --format 'value(status.url)')
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$AI_URL/health")
          [ "$STATUS" = "200" ] && echo "✓ AI Service healthy" || (echo "✗ AI Service unhealthy: $STATUS" && exit 1)

  # ─── MANUAL APPROVAL ─────────────────────────────────────────────
  # Este job depende del GitHub Environment "production" que debe
  # tener "Required reviewers" configurado en Settings → Environments
  deploy-prod:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: smoke-tests
    environment:
      name: production
      url: https://app.projectforge.app
    strategy:
      max-parallel: 1
      matrix:
        service:
          - name: api-gateway
            cloud_run_name: api-gateway-prod
          - name: core-service
            cloud_run_name: core-service-prod
          - name: ai-service
            cloud_run_name: ai-service-prod
          - name: notification-service
            cloud_run_name: notification-service-prod
    steps:
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Deploy ${{ matrix.service.name }} to Production
        run: |
          # Deploy nueva revisión sin enviar tráfico (blue-green)
          gcloud run deploy ${{ matrix.service.cloud_run_name }} \
            --image ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ matrix.service.name }}:${{ env.IMAGE_TAG }} \
            --region ${{ env.REGION }} \
            --project ${{ env.PROJECT_ID }} \
            --platform managed \
            --no-traffic \
            --tag ${{ env.IMAGE_TAG }} \
            --quiet

          # Enviar 100% del tráfico a la nueva revisión tras verificar health
          NEW_URL=$(gcloud run services describe ${{ matrix.service.cloud_run_name }} \
            --region ${{ env.REGION }} --project ${{ env.PROJECT_ID }} \
            --format 'value(status.url)')

          for i in {1..5}; do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$NEW_URL/health" || echo "000")
            if [ "$STATUS" = "200" ]; then
              echo "✓ Health check passed, switching traffic"
              gcloud run services update-traffic ${{ matrix.service.cloud_run_name }} \
                --to-latest \
                --region ${{ env.REGION }} \
                --project ${{ env.PROJECT_ID }} \
                --quiet
              break
            fi
            echo "Attempt $i: status $STATUS, retrying in 15s..."
            sleep 15
          done

          if [ "$STATUS" != "200" ]; then
            echo "✗ Health check failed — mantener versión anterior en tráfico"
            exit 1
          fi

  notify-prod-deploy:
    name: Notify Production Deploy
    runs-on: ubuntu-latest
    needs: deploy-prod
    if: always()
    steps:
      - name: Slack notification
        uses: slackapi/slack-github-action@v1.26.0
        if: ${{ secrets.SLACK_BOT_TOKEN != '' }}
        with:
          payload: |
            {
              "text": "${{ needs.deploy-prod.result == 'success' && '🚀' || '🔥' }} Production deploy ${{ needs.deploy-prod.result }}: ${{ github.event.release.tag_name }}",
              "attachments": [{
                "color": "${{ needs.deploy-prod.result == 'success' && 'good' || 'danger' }}",
                "fields": [
                  {"title": "Version", "value": "${{ github.event.release.tag_name }}", "short": true},
                  {"title": "Release", "value": "${{ github.event.release.html_url }}", "short": false}
                ]
              }]
            }
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

## Consideraciones Críticas

### 1. mypy en CI requiere `FIREBASE_PROJECT_ID`

El `core-service/src/config.py` tiene `firebase_project_id: str = Field(..., ...)` — campo requerido sin default. mypy lo analiza estáticamente pero en runtime la variable env necesita existir. Pasar `FIREBASE_PROJECT_ID: test-project` como env var en los jobs de lint.

### 2. Tests de core-service con pgvector

La imagen `ankane/pgvector:v0.7.0` incluye PostgreSQL 15 + pgvector extension. El conftest crea las tablas con `Base.metadata.create_all` — esto funciona porque las tablas SQLAlchemy están definidas en los models. **Las migraciones Alembic NO se ejecutan en tests** — los modelos SQLAlchemy crean el schema directamente.

### 3. Tests de AI service — solo unit tests en CI

Los tests de integración de AI service (`tests/integration/test_chat.py`, `tests/integration/test_copilot.py`) pueden requerir DB. Por seguridad, ejecutar solo `tests/unit/` en CI. Si se necesitan los de integración, agregar un segundo postgres service similar al de core-service.

### 4. GitHub Environments para aprobación manual

Para que `deploy-prod` requiera aprobación manual:
1. Ir a GitHub repo → Settings → Environments → New environment → "production"
2. Activar "Required reviewers" y añadir a Ricardo como reviewer
3. El workflow se pausará en el job `deploy-prod` hasta que un reviewer apruebe

### 5. pnpm version en action-setup

Verificar la versión exacta de pnpm en el `package.json` raíz o `pnpm-lock.yaml`. Si hay un campo `"packageManager": "pnpm@X.Y.Z"` en `package.json`, usar esa versión exacta en `pnpm/action-setup`. Si no existe, usar `version: 8`.

### 6. Concurrency en ci.yml

El bloque `concurrency` cancela runs anteriores del mismo PR cuando hay un nuevo push. Crítico para ahorrar minutos de Actions en PRs con muchos commits consecutivos.

### 7. Cache scope por servicio en Docker buildx

`cache-from: type=gha,scope=${{ matrix.service.name }}` — el `scope` diferente por servicio evita que el cache de api-gateway (Go) se mezcle con el de core-service (Python). Sin scope, el último build sobreescribe el cache de todos.

## Configuración Manual Requerida (no automatizable por Terraform)

1. **GitHub Environments**: Crear `dev`, `staging`, `production` en Settings → Environments
2. **Required reviewers en production**: Añadir reviewers en el ambiente "production"
3. **GitHub Secrets**: Configurar los 5 secrets listados arriba
4. **SA Key JSON**: El service account debe tener los roles necesarios y la key descargada en formato JSON

## Checklist de Entrega

- [ ] `.github/workflows/ci.yml` creado
- [ ] `.github/workflows/deploy-dev.yml` creado
- [ ] `.github/workflows/deploy-prod.yml` creado
- [ ] Jobs de Python usan `poetry==1.7.1` (versión exacta del Dockerfile)
- [ ] Job `test-core-service` usa `services: postgres: image: ankane/pgvector:v0.7.0`
- [ ] Job `test-ai-service` solo corre `tests/unit/` (no requiere DB)
- [ ] Jobs de Go usan `go-version: '1.23'`
- [ ] Docker builds usan `cache-from/cache-to: type=gha` con scope por servicio
- [ ] `deploy-prod` usa `environment: production` con `--no-traffic` + health check antes de `update-traffic`
- [ ] Slack notification en deploy-dev y deploy-prod (condicional si secret existe)
- [ ] `concurrency.cancel-in-progress: true` en ci.yml
- [ ] YAML válido (validar con `yamllint` o pegando en editor online)
