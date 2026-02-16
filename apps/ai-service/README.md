# AI Service

AI-powered service for ProjectForge featuring RAG (Retrieval Augmented Generation), document embeddings, conversational AI, and intelligent project copilot.

## Features

### 🔍 RAG (Retrieval Augmented Generation)
- **Vector Search**: pgvector-powered semantic search on project documents
- **Smart Embeddings**: Vertex AI textembedding-gecko@004 (768 dimensions)
- **Context-Aware Answers**: Gemini 1.5 Pro for intelligent responses
- **Source Attribution**: Tracks which documents informed each answer

### 📄 Document Management
- **Upload & Process**: Automatic text extraction and chunking
- **Intelligent Chunking**: 512 tokens with 50-token overlap using tiktoken
- **Status Tracking**: pending → processing → completed/failed
- **Multi-tenant Isolation**: Organization-scoped document access

### 💬 Chat Sessions
- **Conversational AI**: Multi-turn conversations with context
- **Persistent History**: Database-stored conversation threads
- **Project Context**: Scoped to specific projects
- **User Sessions**: Track conversations per user

### 🤖 AI Copilot
- **Project Health Analysis**: Automated health scoring and issue detection
- **Risk Detection**: Identifies overdue tasks, milestone delays, resource bottlenecks
- **Timeline Prediction**: ML-based completion estimates
- **Actionable Insights**: AI-generated recommendations

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI Service (FastAPI)                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Documents   │  │     RAG      │  │    Chat      │  │
│  │  - Upload    │  │  - Query     │  │  - Sessions  │  │
│  │  - Chunks    │  │  - Stream    │  │  - Messages  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ Embeddings   │  │   Copilot    │                     │
│  │  - Vertex AI │  │  - Analyze   │                     │
│  │  - Chunker   │  │  - Risks     │                     │
│  └──────────────┘  └──────────────┘                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   PostgreSQL        Vertex AI        Cloud Storage
   + pgvector        (Gemini)         (Documents)
```

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL + pgvector + SQLAlchemy 2.0
- **AI/ML**: Google Vertex AI (Gemini 1.5 Pro, textembedding-gecko@004)
- **Storage**: Cloud Storage
- **Tokenization**: tiktoken (GPT-4 encoding)
- **Validation**: Pydantic v2

## Installation

### Prerequisites
- Python 3.12+
- PostgreSQL 15+ with pgvector extension
- Google Cloud Project with Vertex AI enabled
- Service account with Vertex AI permissions

### Setup

```bash
# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Enable pgvector in PostgreSQL
psql -d projectforge -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations (from project root)
cd ../..
alembic upgrade head

# Start service
cd apps/ai-service
poetry run uvicorn src.main:app --reload --port 8001
```

## API Endpoints

### Documents

```bash
# Upload document
POST /api/v1/documents/
{
  "name": "project-spec.pdf",
  "project_id": "uuid",
  "file_type": "application/pdf",
  "file_size": 1024000,
  "file_path": "gs://bucket/path/to/file.pdf"
}

# Get document with chunks
GET /api/v1/documents/{document_id}?include_chunks=true

# List project documents
GET /api/v1/documents/project/{project_id}?skip=0&limit=20

# Delete document
DELETE /api/v1/documents/{document_id}
```

### RAG (Retrieval Augmented Generation)

```bash
# Query documents
POST /api/v1/rag/query
{
  "question": "What are the key milestones?",
  "project_id": "uuid",
  "max_chunks": 5
}

# Response
{
  "answer": "Based on the documents...",
  "sources": [
    {
      "document_id": "uuid",
      "chunk_id": "uuid",
      "content": "...",
      "similarity": 0.92,
      "chunk_index": 3
    }
  ],
  "confidence": "high",
  "chunks_retrieved": 5
}

# Stream query (real-time response)
POST /api/v1/rag/query/stream
```

### Chat

```bash
# Create chat session
POST /api/v1/chat/sessions
{
  "project_id": "uuid",
  "title": "Project Discussion"
}

# Send message
POST /api/v1/chat/messages
{
  "session_id": "uuid",
  "content": "What's the project status?"
}

# Get session history
GET /api/v1/chat/sessions/{session_id}

# List project sessions
GET /api/v1/chat/projects/{project_id}/sessions

# Delete session
DELETE /api/v1/chat/sessions/{session_id}
```

### AI Copilot

```bash
# Comprehensive analysis
POST /api/v1/copilot/analyze
{
  "project_id": "uuid",
  "include_tasks": true,
  "include_milestones": true
}

# Response
{
  "health": {
    "score": 75,
    "status": "at_risk",
    "issues": ["3 overdue tasks"],
    "task_completion_rate": 0.65
  },
  "risks": [
    {
      "type": "overdue_tasks",
      "severity": "high",
      "description": "5 tasks are overdue",
      "impact": "Timeline may be compromised",
      "mitigation": "Review and reprioritize tasks"
    }
  ],
  "completion_prediction": {
    "predicted_date": "2024-03-15T00:00:00",
    "confidence": "medium",
    "estimated_days_remaining": 30
  },
  "ai_insights": "Key actions: 1. Address overdue tasks..."
}

# Risk analysis
POST /api/v1/copilot/risks?project_id=uuid

# Get suggestions
POST /api/v1/copilot/suggestions?project_id=uuid

# Timeline prediction
POST /api/v1/copilot/timeline?project_id=uuid&include_historical=true
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8001` |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `DATABASE_URL` | PostgreSQL connection URL | - |
| `GCP_PROJECT_ID` | Google Cloud Project ID | - |
| `GCP_LOCATION` | Vertex AI location | `us-central1` |
| `VERTEX_EMBEDDING_MODEL` | Embedding model | `textembedding-gecko@004` |
| `VERTEX_LLM_MODEL` | LLM model | `gemini-1.5-pro` |
| `CHUNK_SIZE` | Max tokens per chunk | `512` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `MAX_CHUNKS_PER_QUERY` | Chunks to retrieve | `5` |
| `GCS_BUCKET_NAME` | Storage bucket | - |

## Development

### Code Quality

```bash
# Format code
poetry run black src/
poetry run isort src/

# Type checking
poetry run mypy src/

# Linting
poetry run ruff check src/

# Run all checks
poetry run black src/ && poetry run isort src/ && poetry run mypy src/ && poetry run ruff check src/
```

### Testing

```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=src tests/

# Watch mode
poetry run pytest-watch
```

## Deployment

### Docker

```bash
# Build image
docker build -t projectforge/ai-service .

# Run container
docker run -p 8001:8001 \
  -e DATABASE_URL="postgresql://..." \
  -e GCP_PROJECT_ID="your-project" \
  -v /path/to/credentials.json:/app/credentials.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  projectforge/ai-service
```

### Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy ai-service \
  --source=. \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=...,GCP_PROJECT_ID=..." \
  --service-account=ai-service@project.iam.gserviceaccount.com
```

## How It Works

### Document Processing Pipeline

1. **Upload**: Document uploaded to Cloud Storage
2. **Extract**: Text extracted (future: Document AI integration)
3. **Chunk**: Text split into 512-token chunks with 50-token overlap
4. **Embed**: Each chunk embedded using Vertex AI (768 dimensions)
5. **Store**: Chunks and embeddings stored in PostgreSQL with pgvector
6. **Status**: Document marked as `completed`

### RAG Query Flow

1. **Embed Query**: User question embedded using same model
2. **Vector Search**: Cosine similarity search in pgvector
3. **Retrieve**: Top 5 most similar chunks retrieved
4. **Build Context**: Chunks assembled into prompt context
5. **Generate**: Gemini 1.5 Pro generates answer
6. **Return**: Answer with source attribution

### Vector Similarity

```sql
-- pgvector cosine distance search
SELECT content, 1 - (embedding <=> $query_embedding) as similarity
FROM document_chunks
WHERE document_id IN (SELECT id FROM documents WHERE project_id = $project_id)
ORDER BY embedding <=> $query_embedding
LIMIT 5;
```

## Database Schema

```sql
-- Documents table
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  organization_id UUID NOT NULL,
  name VARCHAR(255),
  file_path VARCHAR(500),
  file_type VARCHAR(50),
  file_size INTEGER,
  status VARCHAR(50),
  error_message TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Document chunks with vector embeddings
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT,
  chunk_index INTEGER,
  token_count INTEGER,
  embedding vector(768),  -- pgvector
  created_at TIMESTAMP
);

-- Vector similarity index
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);

-- Chat sessions
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY,
  project_id UUID,
  organization_id UUID,
  user_id VARCHAR(255),
  title VARCHAR(255),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Chat messages
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role VARCHAR(20),  -- user, assistant, system
  content TEXT,
  created_at TIMESTAMP
);
```

## Performance Considerations

- **Batch Embeddings**: Process up to 5 texts per API call
- **Vector Index**: IVFFlat index for fast similarity search
- **Connection Pooling**: Async connection pool (5 + 10 overflow)
- **Chunk Caching**: Embeddings stored permanently
- **Streaming**: Support for streaming LLM responses

## Security

- **Multi-tenant Isolation**: All queries filtered by organization_id
- **Header Validation**: Requires X-Organization-ID header from gateway
- **RLS Policies**: Row-level security on database tables
- **No Direct Access**: All requests via API Gateway
- **Service Account**: Dedicated GCP service account with minimal permissions

## Troubleshooting

### Common Issues

**pgvector not installed**
```bash
psql -d projectforge -c "CREATE EXTENSION vector;"
```

**Vertex AI authentication error**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
gcloud auth application-default login
```

**Embedding dimension mismatch**
- Ensure EMBEDDING_DIMENSIONS=768 for textembedding-gecko@004
- Recreate tables if dimension changed

**Slow vector search**
```sql
-- Create IVFFlat index
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

## Future Enhancements

- [ ] Document AI integration for PDF/image extraction
- [ ] Multi-language support
- [ ] Custom fine-tuned embeddings
- [ ] Real-time document processing with Pub/Sub
- [ ] Hybrid search (keyword + semantic)
- [ ] Re-ranking for better relevance
- [ ] Conversation summarization
- [ ] Auto-tagging and categorization

## License

Proprietary - ProjectForge
