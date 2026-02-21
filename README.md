# ProjectForge

> AI-Powered Project Management Platform

ProjectForge is a modern, multi-tenant SaaS platform for project management with intelligent AI capabilities. Built to compete with enterprise solutions like Microsoft Project, it provides organizations with powerful tools to manage clients, projects, tasks, and milestones.

## 🚀 Features

- **Multi-tenant Architecture**: Secure, isolated workspaces for each organization
- **AI Copilot**: Intelligent project assistance powered by Vertex AI
- **RAG-based Q&A**: Ask questions about your project documents
- **Real-time Collaboration**: Live updates with Firestore
- **Gantt Charts**: Visual project timeline management
- **Kanban Boards**: Flexible task management
- **Advanced Reporting**: Comprehensive project insights
- **Integrations**: Slack, Microsoft Teams, and more

## 🏗️ Architecture

ProjectForge uses a microservices architecture deployed on Google Cloud Platform:

```
Frontend (React/Vite) → Cloud Load Balancer → API Gateway (Go)
                                                      ↓
                        ┌─────────────────────────────┼─────────────────────────┐
                        ↓                             ↓                         ↓
                 Core Service                  AI Service           Notification Service
                 (Python/FastAPI)              (Python/FastAPI)            (Go)
                        ↓                             ↓                         ↓
                        └─────────────────────────────┼─────────────────────────┘
                                                      ↓
                              ┌───────────────────────┼───────────────────┐
                              ↓                       ↓                   ↓
                         Cloud SQL              Cloud Storage        Firestore
                      (PostgreSQL+pgvector)      (Documents)        (Realtime)
```

## 🛠️ Tech Stack

### Frontend
- React 18+ with TypeScript
- Vite for fast builds
- TailwindCSS + shadcn/ui
- TanStack Query + Zustand

### Backend
- **API Gateway**: Go 1.22+ (Chi router)
- **Core Service**: Python 3.12+ (FastAPI)
- **AI Service**: Python 3.12+ (FastAPI + Vertex AI)
- **Notification Service**: Go 1.22+

### Data & Infrastructure
- PostgreSQL 15+ with pgvector
- Firestore for real-time sync
- Cloud Storage for documents
- Firebase Auth
- Vertex AI (Gemini 1.5 Pro + Embeddings)
- Terraform for IaC

## 📦 Monorepo Structure

```
projectforge/
├── apps/
│   ├── web/                    # React frontend
│   ├── api-gateway/            # Go API gateway
│   ├── core-service/           # Python core service
│   ├── ai-service/             # Python AI service
│   └── notification-service/   # Go notification service
├── packages/
│   ├── shared-types/           # TypeScript type definitions
│   └── ui-components/          # Shared React components
├── infrastructure/
│   └── terraform/              # Infrastructure as Code
├── migrations/                 # Database migrations
└── scripts/                    # Build and deployment scripts
```

## 🚦 Getting Started

### Prerequisites

- Node.js 20+
- pnpm 9+
- Go 1.22+
- Python 3.12+
- Docker & Docker Compose
- PostgreSQL 15+
- GCP account (for deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rrv-enkisys/projectforge.git
   cd projectforge
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Set up environment variables**
   ```bash
   # Copy example env files
   cp apps/web/.env.example apps/web/.env
   cp apps/core-service/.env.example apps/core-service/.env
   cp apps/ai-service/.env.example apps/ai-service/.env
   ```

4. **Start development services**
   ```bash
   # Start all services
   pnpm dev

   # Or start specific services
   pnpm dev --filter=web
   pnpm dev --filter=core-service
   ```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 Documentation

- [Architecture Documentation](./ARCHITECTURE.md)
- [API Documentation](./docs/api/README.md)
- [Development Guide](./docs/development.md)
- [Deployment Guide](./docs/deployment.md)

## 🧪 Testing

```bash
# Run all tests
pnpm test

# Run tests for specific service
pnpm test --filter=core-service

# Run with coverage
pnpm test --coverage
```

## 🔧 Development Commands

```bash
# Development
pnpm dev                      # Start all services
pnpm build                    # Build all services
pnpm lint                     # Lint all code
pnpm format                   # Format all code

# Database
pnpm db:migrate              # Run migrations
pnpm db:seed                 # Seed test data
pnpm db:reset                # Reset database

# Code generation
pnpm generate:types          # Generate TypeScript types
pnpm generate:api            # Generate API client
```

## 📝 Code Standards

- **Python**: Black, isort, mypy, ruff
- **Go**: gofmt, golangci-lint
- **TypeScript**: ESLint, Prettier

See [.claude/CLAUDE.md](./.claude/CLAUDE.md) for detailed code standards and patterns.

## 🚀 Deployment

### Development
```bash
terraform -chdir=infrastructure/terraform/environments/dev apply
```

### Production
```bash
terraform -chdir=infrastructure/terraform/environments/prod apply
```

See [Deployment Guide](./docs/deployment.md) for detailed instructions.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

## 🔐 CI/CD — GitHub Secrets Required

Configure these secrets in **Settings → Secrets and variables → Actions** before the workflows will run:

| Secret | Description | Required by |
|--------|-------------|-------------|
| `GCP_PROJECT_ID` | GCP project ID (`projectforge-4314f`) | `deploy-dev`, `deploy-prod` |
| `GCP_SA_KEY` | Service Account JSON key with roles: `roles/run.admin`, `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser`, `roles/storage.admin` | `deploy-dev`, `deploy-prod` |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token for deploy notifications (optional) | `deploy-dev`, `deploy-prod` |

### GitHub Environments (manual setup)

Create three environments in **Settings → Environments**:

| Environment | Protection rules | URL |
|-------------|-----------------|-----|
| `dev` | None (auto-deploy on push to main) | `https://dev.projectforge.app` |
| `staging` | None (auto-deploy on release) | `https://staging.projectforge.app` |
| `production` | **Required reviewers** — add at least one reviewer | `https://app.projectforge.app` |

The `production` environment's **Required Reviewers** gate is what enforces manual approval before prod deploy.

### Generating the GCP Service Account Key

```bash
# Create a dedicated SA for GitHub Actions (if not using Workload Identity)
gcloud iam service-accounts create sa-github-actions \
  --display-name "GitHub Actions CI/CD" \
  --project projectforge-4314f

# Grant required roles
for role in roles/run.admin roles/artifactregistry.writer \
            roles/iam.serviceAccountUser roles/storage.admin; do
  gcloud projects add-iam-policy-binding projectforge-4314f \
    --member "serviceAccount:sa-github-actions@projectforge-4314f.iam.gserviceaccount.com" \
    --role "$role"
done

# Download the key (add to GitHub secret GCP_SA_KEY)
gcloud iam service-accounts keys create /tmp/sa-github-actions.json \
  --iam-account sa-github-actions@projectforge-4314f.iam.gserviceaccount.com
cat /tmp/sa-github-actions.json
rm /tmp/sa-github-actions.json
```

> **Security note**: Workload Identity Federation (WIF) is the recommended alternative — it avoids long-lived JSON keys. The workflows have `id-token: write` permission ready for a future WIF migration.

## 📄 License

This project is proprietary software. All rights reserved.

## 👥 Team

Built by the EnkiSys team.

- **Lead Developer**: Ricardo Reyes (ricardo@enkisys.com)

## 🔗 Links

- [Documentation](./docs)
- [Issue Tracker](https://github.com/rrv-enkisys/projectforge/issues)
- [Changelog](./CHANGELOG.md)

---

Made with ❤️ by [EnkiSys](https://enkisys.com)
