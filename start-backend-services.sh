#!/bin/bash
# Start all backend services in tmux

set -e

echo "🚀 Iniciando servicios backend en tmux..."

# Kill existing session if it exists
tmux kill-session -t projectforge-backend 2>/dev/null || true

# Create new tmux session
tmux new-session -d -s projectforge-backend -n core

# Window 0: Core Service (Python/FastAPI)
echo "📦 Configurando Core Service (puerto 8000)..."
tmux send-keys -t projectforge-backend:0 'cd ~/projectforge/apps/core-service' C-m
tmux send-keys -t projectforge-backend:0 'export PATH="$HOME/.local/bin:$PATH"' C-m
tmux send-keys -t projectforge-backend:0 'export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge"' C-m
tmux send-keys -t projectforge-backend:0 'export FIREBASE_PROJECT_ID="projectforge-dev"' C-m
tmux send-keys -t projectforge-backend:0 'export API_PREFIX="/api/v1"' C-m
tmux send-keys -t projectforge-backend:0 'echo "🔵 Installing dependencies..."' C-m
tmux send-keys -t projectforge-backend:0 'poetry install --no-interaction 2>&1 | grep -E "(Installing|Using|Skipping)" | tail -5' C-m
tmux send-keys -t projectforge-backend:0 'echo "✅ Core Service starting on port 8000..."' C-m
tmux send-keys -t projectforge-backend:0 'poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload' C-m

# Window 1: AI Service (Python/FastAPI)
echo "🤖 Configurando AI Service (puerto 8001)..."
tmux new-window -t projectforge-backend:1 -n ai
tmux send-keys -t projectforge-backend:1 'cd ~/projectforge/apps/ai-service' C-m
tmux send-keys -t projectforge-backend:1 'export PATH="$HOME/.local/bin:$PATH"' C-m
tmux send-keys -t projectforge-backend:1 'export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge"' C-m
tmux send-keys -t projectforge-backend:1 'export GCP_PROJECT_ID="projectforge-dev"' C-m
tmux send-keys -t projectforge-backend:1 'export GCP_LOCATION="us-central1"' C-m
tmux send-keys -t projectforge-backend:1 'export API_PREFIX="/api/v1"' C-m
tmux send-keys -t projectforge-backend:1 'export PORT="8001"' C-m
tmux send-keys -t projectforge-backend:1 'echo "🔵 Installing dependencies..."' C-m
tmux send-keys -t projectforge-backend:1 'poetry install --no-interaction 2>&1 | grep -E "(Installing|Using|Skipping)" | tail -5' C-m
tmux send-keys -t projectforge-backend:1 'echo "✅ AI Service starting on port 8001..."' C-m
tmux send-keys -t projectforge-backend:1 'poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload' C-m

# Window 2: API Gateway (Go)
echo "🚪 Configurando API Gateway (puerto 8080)..."
tmux new-window -t projectforge-backend:2 -n gateway
tmux send-keys -t projectforge-backend:2 'cd ~/projectforge/apps/api-gateway' C-m
tmux send-keys -t projectforge-backend:2 'export PATH=$PATH:/usr/local/go/bin' C-m
tmux send-keys -t projectforge-backend:2 'export PORT="8080"' C-m
tmux send-keys -t projectforge-backend:2 'export CORE_SERVICE_URL="http://localhost:8000"' C-m
tmux send-keys -t projectforge-backend:2 'export AI_SERVICE_URL="http://localhost:8001"' C-m
tmux send-keys -t projectforge-backend:2 'export NOTIFICATION_SERVICE_URL="http://localhost:8083"' C-m
tmux send-keys -t projectforge-backend:2 'export FIREBASE_PROJECT_ID="projectforge-dev"' C-m
tmux send-keys -t projectforge-backend:2 'export ENVIRONMENT="development"' C-m
tmux send-keys -t projectforge-backend:2 'echo "🔵 Downloading Go modules..."' C-m
tmux send-keys -t projectforge-backend:2 'go mod download 2>&1 | tail -3' C-m
tmux send-keys -t projectforge-backend:2 'echo "✅ API Gateway starting on port 8080..."' C-m
tmux send-keys -t projectforge-backend:2 'go run cmd/server/main.go' C-m

# Select first window
tmux select-window -t projectforge-backend:0

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Servicios iniciándose en tmux session 'projectforge-backend'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Ventanas tmux:"
echo "  0: core    - Core Service (Python)    - Puerto 8000"
echo "  1: ai      - AI Service (Python)      - Puerto 8001"
echo "  2: gateway - API Gateway (Go)         - Puerto 8080"
echo ""
echo "🎮 Comandos tmux:"
echo "  • Adjuntar:         tmux attach -t projectforge-backend"
echo "  • Cambiar ventana:  Ctrl+B luego 0/1/2"
echo "  • Detach:           Ctrl+B luego d"
echo "  • Ver logs:         Ctrl+B luego [  (q para salir)"
echo "  • Matar sesión:     tmux kill-session -t projectforge-backend"
echo ""
echo "⏳ Los servicios están instalando dependencias..."
echo "   Espera ~30-60 segundos antes de verificar."
echo ""
echo "🔍 Verificar estado:"
echo "   ~/projectforge/check-status.sh"
echo ""
echo "🌐 URLs una vez iniciados:"
echo "   http://localhost:8000/docs  - Core API"
echo "   http://localhost:8001/docs  - AI API"
echo "   http://localhost:8080/health - API Gateway"
echo ""
