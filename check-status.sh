#!/bin/bash
# Check ProjectForge Services Status

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "     ProjectForge - Estado de Servicios"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker services
echo "🐳 Servicios Docker:"
if sudo docker ps --format "table {{.Names}}\t{{.Status}}" | grep projectforge 2>/dev/null; then
    echo ""
else
    echo -e "${RED}  ❌ No hay contenedores Docker corriendo${NC}"
    echo ""
fi

# Check Application ports
echo "🚀 Servicios de Aplicación:"

check_port() {
    local port=$1
    local name=$2
    if sudo ss -tlnp | grep -q ":$port "; then
        echo -e "  ${GREEN}✅ $name${NC} - http://localhost:$port"
    else
        echo -e "  ${RED}❌ $name${NC} - No corriendo en puerto $port"
    fi
}

check_port 3000 "Frontend (React)"
check_port 5173 "Frontend (Vite)"
check_port 8000 "Core Service (Python)"
check_port 8001 "AI Service (Python)"
check_port 8080 "API Gateway (Go)"

echo ""

# Check PostgreSQL
echo "🗄️  Base de Datos:"
if sudo docker exec projectforge-postgres psql -U postgres -d projectforge -c "SELECT COUNT(*) FROM organizations;" 2>/dev/null | grep -q "1"; then
    echo -e "  ${GREEN}✅ PostgreSQL${NC} - Tablas creadas y organización inicializada"
else
    echo -e "  ${YELLOW}⚠️  PostgreSQL${NC} - Corriendo pero sin datos"
fi

# Check pgvector
if sudo docker exec projectforge-postgres psql -U postgres -d projectforge -c "\dx" 2>/dev/null | grep -q "vector"; then
    echo -e "  ${GREEN}✅ pgvector${NC} - Extensión habilitada"
else
    echo -e "  ${RED}❌ pgvector${NC} - No habilitado"
fi

echo ""

# External IP
IP=$(curl -s ifconfig.me)
echo "🌐 Acceso Externo:"
echo "  IP: $IP"
echo ""
echo "  URLs de Acceso:"
echo "  • Frontend:    http://$IP:3000"
echo "  • Core API:    http://$IP:8000/docs"
echo "  • AI API:      http://$IP:8001/docs"
echo "  • API Gateway: http://$IP:8080/health"
echo ""

# Firewall status
echo "🔓 Estado del Firewall:"
if gcloud compute firewall-rules describe projectforge-dev 2>/dev/null | grep -q "allowed"; then
    echo -e "  ${GREEN}✅ Reglas de firewall configuradas${NC}"
else
    echo -e "  ${YELLOW}⚠️  Necesitas abrir puertos en GCP${NC}"
    echo "  Ejecuta: gcloud compute firewall-rules create projectforge-dev \\"
    echo "             --allow tcp:3000,tcp:5173,tcp:8080,tcp:8000,tcp:8001 \\"
    echo "             --source-ranges 0.0.0.0/0"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
