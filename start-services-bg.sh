#!/bin/bash
# Start services in background using nohup

set -e

cd ~/projectforge

echo "🚀 Iniciando servicios en background..."

# Function to check if port is in use
port_in_use() {
    sudo netstat -tlnp 2>/dev/null | grep -q ":$1 "
}

# Function to stop service on port
stop_service() {
    local port=$1
    local pid=$(sudo netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d/ -f1)
    if [ ! -z "$pid" ]; then
        echo "  Deteniendo servicio en puerto $port (PID: $pid)"
        sudo kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# Stop existing services
echo "🛑 Deteniendo servicios existentes..."
stop_service 8000
stop_service 8001
stop_service 8080

# Create logs directory
mkdir -p ~/projectforge/logs

# Start Core Service
echo "📦 Iniciando Core Service (puerto 8000)..."
cd ~/projectforge/apps/core-service

# Install dependencies first
export PATH="$HOME/.local/bin:$PATH"
echo "  Installing dependencies..."
poetry install --quiet 2>&1 | grep -E "(Installing|Creating)" | tail -5

# Start service
nohup poetry run uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > ~/projectforge/logs/core-service.log 2>&1 &

CORE_PID=$!
echo "  ✅ Core Service iniciado (PID: $CORE_PID)"

# Start AI Service
echo "🤖 Iniciando AI Service (puerto 8001)..."
cd ~/projectforge/apps/ai-service

# Install dependencies
echo "  Installing dependencies..."
poetry install --quiet 2>&1 | grep -E "(Installing|Creating)" | tail -5

# Start service
nohup poetry run uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --reload \
    > ~/projectforge/logs/ai-service.log 2>&1 &

AI_PID=$!
echo "  ✅ AI Service iniciado (PID: $AI_PID)"

# Start API Gateway
echo "🚪 Iniciando API Gateway (puerto 8080)..."
cd ~/projectforge/apps/api-gateway

# Download Go modules
echo "  Downloading Go modules..."
export PATH=$PATH:/usr/local/go/bin
go mod download 2>&1 | tail -3

# Start service
export PORT=8080
export CORE_SERVICE_URL="http://localhost:8000"
export AI_SERVICE_URL="http://localhost:8001"
export FIREBASE_PROJECT_ID="projectforge-dev"
export ENVIRONMENT="development"

nohup go run cmd/server/main.go \
    > ~/projectforge/logs/api-gateway.log 2>&1 &

GATEWAY_PID=$!
echo "  ✅ API Gateway iniciado (PID: $GATEWAY_PID)"

# Save PIDs
echo "$CORE_PID" > ~/projectforge/logs/core-service.pid
echo "$AI_PID" > ~/projectforge/logs/ai-service.pid
echo "$GATEWAY_PID" > ~/projectforge/logs/api-gateway.pid

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Servicios iniciados en background"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 PIDs:"
echo "  Core Service:  $CORE_PID"
echo "  AI Service:    $AI_PID"
echo "  API Gateway:   $GATEWAY_PID"
echo ""
echo "📝 Logs:"
echo "  tail -f ~/projectforge/logs/core-service.log"
echo "  tail -f ~/projectforge/logs/ai-service.log"
echo "  tail -f ~/projectforge/logs/api-gateway.log"
echo ""
echo "⏳ Esperando que los servicios inicien (~30 segundos)..."
sleep 30

echo ""
echo "🔍 Verificando estado..."
~/projectforge/check-status.sh
