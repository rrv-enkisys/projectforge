# API Gateway

API Gateway for ProjectForge - handles authentication, rate limiting, and request routing to backend services.

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         API Gateway                 │
│  ┌───────────────────────────────┐  │
│  │  Middleware Chain:            │  │
│  │  1. CORS                      │  │
│  │  2. Auth (Firebase JWT)       │  │
│  │  3. Tenant (Org context)      │  │
│  │  4. Rate Limit                │  │
│  │  5. Logging                   │  │
│  └───────────────────────────────┘  │
│              │                       │
│              ▼                       │
│      ┌──────────────┐               │
│      │ Proxy Handler│               │
│      └──────┬───────┘               │
└─────────────┼───────────────────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌──────────┐    ┌─────────────┐
│  Core    │    │ AI Service  │
│ Service  │    │             │
└──────────┘    └─────────────┘
```

## Features

- **Firebase Authentication**: JWT token validation
- **Multi-tenant**: Organization context extraction and forwarding
- **Rate Limiting**: Per-organization request rate limiting
- **Structured Logging**: JSON logs with request context
- **CORS**: Configurable CORS for development and production
- **Reverse Proxy**: Routes requests to backend services
- **Graceful Shutdown**: Proper cleanup on shutdown

## Project Structure

```
apps/api-gateway/
├── cmd/
│   └── server/
│       └── main.go              # Application entry point
├── internal/
│   ├── config/
│   │   └── config.go            # Configuration management
│   ├── firebase/
│   │   └── client.go            # Firebase Admin SDK client
│   ├── handler/
│   │   ├── health.go            # Health check handler
│   │   └── proxy.go             # Reverse proxy handler
│   └── middleware/
│       ├── auth.go              # Firebase JWT authentication
│       ├── cors.go              # CORS middleware
│       ├── logging.go           # Structured logging
│       ├── ratelimit.go         # Rate limiting per org
│       └── tenant.go            # Multi-tenant context
├── pkg/
│   └── response/
│       └── json.go              # JSON response helpers
├── .env.example                 # Environment variables template
├── Dockerfile                   # Container configuration
├── go.mod                       # Go module definition
└── README.md                    # This file
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8080` |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `CORE_SERVICE_URL` | Core service URL | `http://localhost:8000` |
| `AI_SERVICE_URL` | AI service URL | `http://localhost:8001` |
| `FIREBASE_PROJECT_ID` | Firebase project ID | - |
| `FIREBASE_CREDENTIALS` | Path to Firebase credentials JSON | - |
| `RATE_LIMIT_RPS` | Requests per second per org | `100` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## Routes

### Public Routes
- `GET /health` - Health check endpoint

### Authenticated Routes (require Bearer token)

All routes under `/api/v1` require Firebase JWT authentication.

**Core Service Routes:**
- `/api/v1/organizations/*` → Core Service
- `/api/v1/clients/*` → Core Service
- `/api/v1/projects/*` → Core Service
- `/api/v1/tasks/*` → Core Service
- `/api/v1/milestones/*` → Core Service
- `/api/v1/users/*` → Core Service

**AI Service Routes:**
- `/api/v1/documents/*` → AI Service
- `/api/v1/chat/*` → AI Service

## Request Flow

1. **CORS**: Handle preflight requests
2. **Auth**: Validate Firebase JWT token from `Authorization: Bearer <token>`
3. **Tenant**: Extract organization context from claims or `X-Organization-ID` header
4. **Rate Limit**: Check rate limit for organization
5. **Logging**: Log request with context
6. **Proxy**: Forward request to backend service with headers:
   - `X-Organization-ID`: Organization ID
   - `X-User-ID`: User Firebase UID
   - `X-User-Email`: User email
   - `X-User-Role`: User role in organization

## Development

### Prerequisites
- Go 1.22+
- Firebase project with Admin SDK credentials

### Setup

1. Copy environment file:
```bash
cp .env.example .env
```

2. Update `.env` with your configuration

3. Install dependencies:
```bash
go mod download
```

4. Run the server:
```bash
go run cmd/server/main.go
```

### Build

```bash
go build -o gateway cmd/server/main.go
```

### Docker

Build:
```bash
docker build -t projectforge/api-gateway .
```

Run:
```bash
docker run -p 8080:8080 --env-file .env projectforge/api-gateway
```

## Testing

### Health Check
```bash
curl http://localhost:8080/health
```

### Authenticated Request
```bash
curl -H "Authorization: Bearer <firebase-token>" \
     -H "X-Organization-ID: <org-uuid>" \
     http://localhost:8080/api/v1/projects
```

## Middleware Details

### Auth Middleware
- Extracts Bearer token from `Authorization` header
- Validates token with Firebase Admin SDK
- Adds user context to request: `user_uid`, `user_email`, `user_claims`

### Tenant Middleware
- Extracts organization ID from:
  1. `X-Organization-ID` header (priority)
  2. Custom claims `organization_id`
  3. First organization from `organizations` array in claims
- Extracts user role for the organization
- Forwards headers to downstream services

### Rate Limit Middleware
- Per-organization rate limiting
- Default: 100 RPS with burst of 200
- Falls back to IP-based limiting if no organization context

### Logging Middleware
- Structured JSON logs
- Includes: request ID, method, path, status, duration, user context
- Log level based on response status (error/warn/info)

## Error Responses

All errors return JSON in this format:
```json
{
  "error": "error_code",
  "message": "Human-readable message"
}
```

Common errors:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `429 Too Many Requests`: Rate limit exceeded
- `502 Bad Gateway`: Backend service unavailable
- `504 Gateway Timeout`: Backend service timeout
