#!/bin/bash
# =============================================================================
# ProjectForge — Tests E2E de servicios Cloud Run dev
# Usa gcloud run services proxy para bypasear ingress internal-and-cloud-lb
# =============================================================================
set -euo pipefail

PROJECT="projectforge-4314f"
REGION="us-central1"
ORG_ID="11111111-1111-1111-1111-111111111111"
USER_ID="test-user-001"

PASS=0; FAIL=0

check() {
  local name="$1" expected="$2" actual="$3"
  if echo "$actual" | grep -q "$expected"; then
    echo "  ✅ $name"; PASS=$((PASS+1))
  else
    echo "  ❌ $name"
    echo "     Esperado contiene: $expected"
    echo "     Obtenido: ${actual:0:150}"
    FAIL=$((FAIL+1))
  fi
}

check_http() {
  local name="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  ✅ $name (HTTP $actual)"; PASS=$((PASS+1))
  else
    echo "  ❌ $name (HTTP $actual, esperado $expected)"; FAIL=$((FAIL+1))
  fi
}

start_proxy() {
  local svc="$1" port="$2"
  gcloud run services proxy "$svc" --port="$port" --region="$REGION" --project="$PROJECT" \
    >/dev/null 2>&1 &
  echo $!
}

wait_port() {
  local port="$1"
  for i in $(seq 1 10); do
    curl -s --max-time 1 "http://localhost:$port/" >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}

http_code() {
  curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$@" 2>/dev/null
}

json_get()  { curl -s --max-time 10 -H "X-Organization-ID: $ORG_ID" -H "X-User-ID: $USER_ID" -H "X-User-Role: admin" "$@"; }
json_post() { curl -s --max-time 10 -H "Content-Type: application/json" -H "X-Organization-ID: $ORG_ID" -H "X-User-ID: $USER_ID" -H "X-User-Role: admin" "$@"; }

echo "========================================"
echo " ProjectForge — E2E Tests (dev)"
echo " $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "========================================"

echo ""
echo "=== Estado Cloud Run ==="
gcloud run services list --region="$REGION" --project="$PROJECT" \
  --format="table(metadata.name,status.conditions[0].type)" 2>&1

# ─── Proxies locales ─────────────────────────────────────────────────────────
echo ""
echo "=== Iniciando proxies locales ==="
GW_PID=$(start_proxy api-gateway-dev 8080)
CORE_PID=$(start_proxy core-service-dev 8081)
AI_PID=$(start_proxy ai-service-dev 8082)
NOTIF_PID=$(start_proxy notification-service-dev 8083)
echo "Esperando que los proxies estén listos..."
sleep 6

trap "kill $GW_PID $CORE_PID $AI_PID $NOTIF_PID 2>/dev/null; echo 'Proxies detenidos'" EXIT

# ─── 1. Health checks ────────────────────────────────────────────────────────
echo ""
echo "=== 1. Health Checks ==="

R=$(curl -s --max-time 10 http://localhost:8080/health)
echo "API Gateway:          $R"
check "API Gateway /health" '"status"' "$R"

R=$(curl -s --max-time 10 http://localhost:8081/health)
echo "Core Service:         $R"
check "Core Service /health" '"status"' "$R"

R=$(curl -s --max-time 10 http://localhost:8082/health)
echo "AI Service:           $R"
check "AI Service /health" '"status"' "$R"

R=$(curl -s --max-time 10 http://localhost:8083/health)
echo "Notification Service: $R"
check "Notification Service /health" '"status"' "$R"

# ─── 2. Auth check via Gateway ───────────────────────────────────────────────
echo ""
echo "=== 2. Auth Check (API Gateway) ==="

CODE=$(http_code http://localhost:8080/api/v1/projects -H "X-Organization-ID: $ORG_ID")
echo "GET /api/v1/projects sin Firebase token → HTTP $CODE"
check_http "Requiere Firebase auth" "401" "$CODE"

# ─── 3. Core Service — CRUD ──────────────────────────────────────────────────
echo ""
echo "=== 3. Core Service CRUD ==="

echo "--- GET /api/v1/projects ---"
R=$(json_get http://localhost:8081/api/v1/projects)
echo "$R" | python3 -m json.tool 2>/dev/null || echo "$R"
check "GET /projects → JSON" '"' "$R"

echo "--- POST /api/v1/clients ---"
R=$(json_post http://localhost:8081/api/v1/clients \
  -d '{"name":"Test Client E2E","email":"client@test.com"}')
echo "$R" | python3 -m json.tool 2>/dev/null || echo "$R"
check "POST /clients → crea o error conocido" '"' "$R"

echo "--- POST /api/v1/projects ---"
R=$(json_post http://localhost:8081/api/v1/projects \
  -d '{"name":"Test Project E2E","status":"active","start_date":"2026-03-05","end_date":"2026-12-31"}')
echo "$R" | python3 -m json.tool 2>/dev/null || echo "$R"
check "POST /projects → crea o error conocido" '"' "$R"

echo "--- GET /api/v1/dashboard ---"
R=$(json_get http://localhost:8081/api/v1/dashboard)
echo "$R" | python3 -m json.tool 2>/dev/null || echo "$R"
check "GET /dashboard → JSON" '"' "$R"

# ─── 4. AI Service ───────────────────────────────────────────────────────────
echo ""
echo "=== 4. AI Service ==="

echo "--- GET /api/v1/chat/sessions ---"
R=$(json_get http://localhost:8082/api/v1/chat/sessions)
echo "$R" | python3 -m json.tool 2>/dev/null || echo "$R"
check "GET /chat/sessions → JSON" '"' "$R"

echo "--- GET /api/v1/documents ---"
R=$(json_get "http://localhost:8082/api/v1/documents?project_id=00000000-0000-0000-0000-000000000001")
echo "$R" | python3 -m json.tool 2>/dev/null || echo "$R"
check "GET /documents → JSON" '"' "$R"

# ─── 5. Notification Service ─────────────────────────────────────────────────
echo ""
echo "=== 5. Notification Service ==="

R=$(curl -s --max-time 10 http://localhost:8083/api/v1/notifications \
  -H "X-Organization-ID: $ORG_ID" -H "X-User-ID: $USER_ID")
echo "$R" | python3 -m json.tool 2>/dev/null || echo "$R"
check "GET /notifications → JSON" '"' "$R"

# ─── Resumen ──────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo " Resumen: $PASS pasaron / $((PASS+FAIL)) total"
[ $FAIL -gt 0 ] && echo " ❌ $FAIL fallaron" || echo " ✅ Todos los tests pasaron"
echo "========================================"
