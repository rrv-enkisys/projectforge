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
