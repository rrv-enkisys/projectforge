#!/bin/bash
# Start ProjectForge in Development Mode
# Este script inicia solo los servicios que están implementados

set -e

cd "$(dirname "$0")"

echo "🚀 Starting ProjectForge Development Environment"
echo "================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file. Please edit it with your credentials.${NC}"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Start only PostgreSQL and Redis with Docker
echo -e "${GREEN}🐳 Starting PostgreSQL and Redis...${NC}"
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
until docker exec projectforge-postgres pg_isready -U postgres > /dev/null 2>&1; do
    sleep 1
done
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"

# Run migrations
echo -e "${GREEN}📊 Running database migrations...${NC}"
cd migrations
if [ -f "001_initial_schema.sql" ]; then
    docker exec -i projectforge-postgres psql -U postgres -d projectforge < 001_initial_schema.sql 2>/dev/null || echo "  Schema already exists, skipping..."
fi
if [ -f "002_add_pgvector.sql" ]; then
    docker exec -i projectforge-postgres psql -U postgres -d projectforge < 002_add_pgvector.sql 2>/dev/null || echo "  pgvector already enabled, skipping..."
fi
if [ -f "003_add_documents_chunks.sql" ]; then
    docker exec -i projectforge-postgres psql -U postgres -d projectforge < 003_add_documents_chunks.sql 2>/dev/null || echo "  Documents tables already exist, skipping..."
fi
if [ -f "004_add_chat_tables.sql" ]; then
    docker exec -i projectforge-postgres psql -U postgres -d projectforge < 004_add_chat_tables.sql 2>/dev/null || echo "  Chat tables already exist, skipping..."
fi
cd ..
echo -e "${GREEN}✅ Migrations complete${NC}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Services Started Successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📦 Docker Services:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis:      localhost:6379"
echo ""
echo "🎯 Next Steps - Start these services in separate terminals:"
echo ""
echo "  Terminal 1 - Core Service (Python):"
echo "    cd ~/projectforge/apps/core-service"
echo "    poetry install"
echo "    poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "  Terminal 2 - AI Service (Python):"
echo "    cd ~/projectforge/apps/ai-service"
echo "    poetry install"
echo "    poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload"
echo ""
echo "  Terminal 3 - API Gateway (Go):"
echo "    cd ~/projectforge/apps/api-gateway"
echo "    go mod download"
echo "    go run cmd/server/main.go"
echo ""
echo "  Terminal 4 - Frontend (React):"
echo "    cd ~/projectforge/apps/web"
echo "    pnpm install"
echo "    pnpm dev --host 0.0.0.0"
echo ""
echo -e "${YELLOW}💡 Tip: Usa 'tmux' o 'screen' para múltiples terminales${NC}"
echo ""
echo "🌐 Access URLs (replace VM_IP with your VM's external IP):"
echo "  • Frontend:    http://VM_IP:5173"
echo "  • API Gateway: http://VM_IP:8080"
echo "  • Core API:    http://VM_IP:8000/docs"
echo "  • AI API:      http://VM_IP:8001/docs"
echo ""
echo "To get your VM external IP: curl -s ifconfig.me"
echo ""
