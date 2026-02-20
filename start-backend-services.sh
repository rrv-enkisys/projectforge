#!/bin/bash
# Start all ProjectForge backend services
# Run this after a VM restart to bring everything up

set -e

PROJECTFORGE_DIR="$HOME/projectforge"
GCP_PROJECT_ID="projectforge-4314f"
GCP_LOCATION="us-central1"
FIREBASE_PROJECT_ID="projectforge-4314f"
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ProjectForge - Iniciando Servicios"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Start PostgreSQL via Docker
echo "🐳 Iniciando PostgreSQL..."
cd "$PROJECTFORGE_DIR"
docker compose up -d postgres
echo "  Esperando a que PostgreSQL esté listo..."
sleep 3
if docker exec projectforge-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL listo en puerto 5432"
else
    echo "  ⚠️  PostgreSQL tardando en iniciar, espera unos segundos más..."
fi
echo ""

# Step 2: Kill existing tmux session if any
tmux kill-session -t projectforge-backend 2>/dev/null || true

# Step 3: Create new tmux session
echo "🚀 Iniciando servicios en tmux..."
tmux new-session -d -s projectforge-backend -n core

# Window 0: Core Service (Python/FastAPI)
echo "  [0] Core Service    → puerto 8000"
tmux send-keys -t projectforge-backend:0 "cd $PROJECTFORGE_DIR/apps/core-service" C-m
tmux send-keys -t projectforge-backend:0 "export PATH=\"\$HOME/.local/bin:\$PATH\"" C-m
tmux send-keys -t projectforge-backend:0 "export DATABASE_URL=\"$DATABASE_URL\"" C-m
tmux send-keys -t projectforge-backend:0 "export FIREBASE_PROJECT_ID=\"$FIREBASE_PROJECT_ID\"" C-m
tmux send-keys -t projectforge-backend:0 "export API_PREFIX=\"/api/v1\"" C-m
tmux send-keys -t projectforge-backend:0 "export ENVIRONMENT=\"development\"" C-m
tmux send-keys -t projectforge-backend:0 "poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 | tee /tmp/core-service.log" C-m

# Window 1: AI Service (Python/FastAPI)
echo "  [1] AI Service      → puerto 8001"
tmux new-window -t projectforge-backend:1 -n ai
tmux send-keys -t projectforge-backend:1 "cd $PROJECTFORGE_DIR/apps/ai-service" C-m
tmux send-keys -t projectforge-backend:1 "export PATH=\"\$HOME/.local/bin:\$PATH\"" C-m
tmux send-keys -t projectforge-backend:1 "export DATABASE_URL=\"$DATABASE_URL\"" C-m
tmux send-keys -t projectforge-backend:1 "export GCP_PROJECT_ID=\"$GCP_PROJECT_ID\"" C-m
tmux send-keys -t projectforge-backend:1 "export GCP_LOCATION=\"$GCP_LOCATION\"" C-m
tmux send-keys -t projectforge-backend:1 "export VERTEX_EMBEDDING_MODEL=\"text-embedding-004\"" C-m
tmux send-keys -t projectforge-backend:1 "export VERTEX_LLM_MODEL=\"gemini-2.0-flash-exp\"" C-m
tmux send-keys -t projectforge-backend:1 "export API_PREFIX=\"/api/v1\"" C-m
tmux send-keys -t projectforge-backend:1 "export PORT=\"8001\"" C-m
tmux send-keys -t projectforge-backend:1 "export ENVIRONMENT=\"development\"" C-m
tmux send-keys -t projectforge-backend:1 "poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload 2>&1 | tee /tmp/ai-service.log" C-m

# Window 2: Notification Service (Go)
echo "  [2] Notification    → puerto 8083"
tmux new-window -t projectforge-backend:2 -n notification
tmux send-keys -t projectforge-backend:2 "cd $PROJECTFORGE_DIR/apps/notification-service" C-m
tmux send-keys -t projectforge-backend:2 "export PATH=\$PATH:/usr/local/go/bin" C-m
tmux send-keys -t projectforge-backend:2 "export PORT=\"8083\"" C-m
tmux send-keys -t projectforge-backend:2 "export DATABASE_URL=\"postgresql://postgres:postgres@localhost:5432/projectforge\"" C-m
tmux send-keys -t projectforge-backend:2 "export FIREBASE_PROJECT_ID=\"$FIREBASE_PROJECT_ID\"" C-m
tmux send-keys -t projectforge-backend:2 "export ENVIRONMENT=\"development\"" C-m
tmux send-keys -t projectforge-backend:2 "go run cmd/server/main.go 2>&1 | tee /tmp/notification-service.log" C-m

# Window 3: API Gateway (Go)
echo "  [3] API Gateway     → puerto 8080"
tmux new-window -t projectforge-backend:3 -n gateway
tmux send-keys -t projectforge-backend:3 "cd $PROJECTFORGE_DIR/apps/api-gateway" C-m
tmux send-keys -t projectforge-backend:3 "export PATH=\$PATH:/usr/local/go/bin" C-m
tmux send-keys -t projectforge-backend:3 "export PORT=\"8080\"" C-m
tmux send-keys -t projectforge-backend:3 "export CORE_SERVICE_URL=\"http://localhost:8000\"" C-m
tmux send-keys -t projectforge-backend:3 "export AI_SERVICE_URL=\"http://localhost:8001\"" C-m
tmux send-keys -t projectforge-backend:3 "export NOTIFICATION_SERVICE_URL=\"http://localhost:8083\"" C-m
tmux send-keys -t projectforge-backend:3 "export FIREBASE_PROJECT_ID=\"$FIREBASE_PROJECT_ID\"" C-m
tmux send-keys -t projectforge-backend:3 "export ENVIRONMENT=\"development\"" C-m
tmux send-keys -t projectforge-backend:3 "go run cmd/server/main.go 2>&1 | tee /tmp/gateway.log" C-m

# Select first window
tmux select-window -t projectforge-backend:0

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Servicios iniciados en tmux 'projectforge-backend'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Puertos:  8000 (core)  8001 (ai)  8080 (gateway)  8083 (notifications)"
echo ""
echo "  Comandos tmux:"
echo "    tmux attach -t projectforge-backend   # entrar"
echo "    Ctrl+B + 0/1/2/3                      # cambiar ventana"
echo "    Ctrl+B + d                            # salir sin cerrar"
echo ""
echo "  Logs en tiempo real:"
echo "    tail -f /tmp/core-service.log"
echo "    tail -f /tmp/ai-service.log"
echo "    tail -f /tmp/notification-service.log"
echo "    tail -f /tmp/gateway.log"
echo ""
echo "  Verificar estado:"
echo "    $PROJECTFORGE_DIR/check-status.sh"
echo ""
echo "  ⏳ Espera ~15 segundos para que todos inicien."
echo "     Luego prueba: curl http://localhost:8080/health"
echo ""
