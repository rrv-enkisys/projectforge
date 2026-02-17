#!/bin/bash
# Start backend services in tmux (simplified version)

set -e

echo "🚀 Iniciando servicios backend..."

# Kill existing session
tmux kill-session -t pf 2>/dev/null || true

# Create session with Core Service
tmux new-session -d -s pf -n core "cd ~/projectforge/apps/core-service && \
export PATH=\$HOME/.local/bin:\$PATH && \
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge' && \
export FIREBASE_PROJECT_ID='projectforge-dev' && \
export API_PREFIX='/api/v1' && \
echo '🔵 Installing Core Service dependencies...' && \
poetry install && \
echo '✅ Starting Core Service on port 8000...' && \
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

# Create window for AI Service
tmux new-window -t pf:1 -n ai "cd ~/projectforge/apps/ai-service && \
export PATH=\$HOME/.local/bin:\$PATH && \
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge' && \
export GCP_PROJECT_ID='projectforge-dev' && \
export GCP_LOCATION='us-central1' && \
export API_PREFIX='/api/v1' && \
export PORT='8001' && \
echo '🔵 Installing AI Service dependencies...' && \
poetry install && \
echo '✅ Starting AI Service on port 8001...' && \
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload"

# Create window for API Gateway
tmux new-window -t pf:2 -n gateway "cd ~/projectforge/apps/api-gateway && \
export PATH=\$PATH:/usr/local/go/bin && \
export PORT='8080' && \
export CORE_SERVICE_URL='http://localhost:8000' && \
export AI_SERVICE_URL='http://localhost:8001' && \
export FIREBASE_PROJECT_ID='projectforge-dev' && \
export ENVIRONMENT='development' && \
echo '🔵 Downloading Go modules...' && \
go mod download && \
echo '✅ Starting API Gateway on port 8080...' && \
go run cmd/server/main.go"

tmux select-window -t pf:0

echo ""
echo "✅ Servicios iniciados en tmux!"
echo ""
echo "Ver sesión:      tmux attach -t pf"
echo "Cambiar ventana: Ctrl+B → 0/1/2"
echo "Detach:          Ctrl+B → d"
echo ""
echo "⏳ Instalando dependencias... Espera ~60 segundos"
echo ""
