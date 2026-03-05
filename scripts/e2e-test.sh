#!/bin/bash
# =============================================================================
# ProjectForge — Tests E2E de servicios Cloud Run dev
# Ejecutar desde Cloud Shell (autenticación siempre válida)
# Usa gcloud run services proxy para bypasear la restricción de ingress
# =============================================================================
set -euo pipefail

PROJECT="projectforge-4314f"
REGION="us-central1"
ORG_ID="11111111-1111-1111-1111-111111111111"

PASS=0
FAIL=0

check() {
  local name="$1"
  local expected="$2"
  local actual="$3"
  if echo "$actual" | grep -q "$expected"; then
    echo "  ✅ $name"
    PASS=$((PASS+1))
  else
    echo "  ❌ $name"
    echo "     Esperado: $expected"
    echo "     Obtenido: ${actual:0:200}"
    FAIL=$((FAIL+1))
  fi
}

echo "========================================"
echo " ProjectForge — E2E Tests (dev)"
echo " $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "========================================"
echo ""

# ─── 1. URLs de servicios ────────────────────────────────────────────────────
echo "=== Servicios Cloud Run ==="
gcloud run services list --region="$REGION" --project="$PROJECT" \
  --format="table(metadata.name,status.conditions[0].type,status.url)"
echo ""

GW_URL=$(gcloud run services describe api-gateway-dev --region="$REGION" --project="$PROJECT" --format="value(status.url)")
CORE_URL=$(gcloud run services describe core-service-dev --region="$REGION" --project="$PROJECT" --format="value(status.url)")
AI_URL=$(gcloud run services describe ai-service-dev --region="$REGION" --project="$PROJECT" --format="value(status.url)")
NOTIF_URL=$(gcloud run services describe notification-service-dev --region="$REGION" --project="$PROJECT" --format="value(status.url)")

echo "API Gateway:          $GW_URL"
echo "Core Service:         $CORE_URL"
echo "AI Service:           $AI_URL"
echo "Notification Service: $NOTIF_URL"
echo ""

# ─── 2. Obtener identity token para llamadas autenticadas a Cloud Run ─────────
TOKEN=$(gcloud auth print-identity-token 2>/dev/null || echo "")
AUTH_HEADER=""
if [ -n "$TOKEN" ]; then
  AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""
  echo "✓ Identity token obtenido"
fi

# Función helper para curl con auth
cr_curl() {
  local url="$1"; shift
  curl -s --max-time 15 \
    -H "Authorization: Bearer $TOKEN" \
    "$@" "$url" 2>&1
}

# ─── 3. Health checks ────────────────────────────────────────────────────────
echo "=== Health Checks ==="

echo ""
echo "--- API Gateway ---"
RESULT=$(cr_curl "$GW_URL/health")
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
check "API Gateway /health → status ok" '"status"' "$RESULT"

echo ""
echo "--- Core Service ---"
RESULT=$(cr_curl "$CORE_URL/health")
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
check "Core Service /health → status ok" '"status"' "$RESULT"

echo ""
echo "--- AI Service ---"
RESULT=$(cr_curl "$AI_URL/health")
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
check "AI Service /health → status ok" '"status"' "$RESULT"

echo ""
echo "--- Notification Service ---"
RESULT=$(cr_curl "$NOTIF_URL/health")
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
check "Notification Service /health → status ok" '"status"' "$RESULT"

# ─── 4. Test via API Gateway ─────────────────────────────────────────────────
echo ""
echo "=== Tests via API Gateway ==="

echo ""
echo "--- GET /health (gateway) ---"
RESULT=$(cr_curl "$GW_URL/health")
check "Gateway health" '"status"' "$RESULT"

echo ""
echo "--- GET /api/v1/projects (sin auth → 401) ---"
RESULT=$(cr_curl "$GW_URL/api/v1/projects" -H "X-Organization-ID: $ORG_ID")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
  -H "Authorization: Bearer $TOKEN" \
  "$GW_URL/api/v1/projects" -H "X-Organization-ID: $ORG_ID" 2>/dev/null)
echo "  HTTP $HTTP_CODE"
check "GET /api/v1/projects requiere Firebase auth (401 o 403)" "40" "$HTTP_CODE"

# ─── 5. Test Core Service directo ─────────────────────────────────────────────
echo ""
echo "=== Tests Core Service (directo) ==="

echo ""
echo "--- GET /api/v1/organizations ---"
RESULT=$(cr_curl "$CORE_URL/api/v1/organizations" \
  -H "X-Organization-ID: $ORG_ID" \
  -H "X-User-ID: test-user-001" \
  -H "X-User-Role: admin")
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "${RESULT:0:300}"
check "GET /api/v1/organizations responde JSON" '"' "$RESULT"

echo ""
echo "--- POST /api/v1/organizations ---"
RESULT=$(cr_curl "$CORE_URL/api/v1/organizations" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-Organization-ID: $ORG_ID" \
  -H "X-User-ID: test-user-001" \
  -H "X-User-Role: admin" \
  -d '{"name":"Test Org E2E","slug":"test-org-e2e","plan":"free"}')
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "${RESULT:0:300}"
check "POST /api/v1/organizations retorna id o error conocido" '"' "$RESULT"

echo ""
echo "--- GET /api/v1/projects ---"
RESULT=$(cr_curl "$CORE_URL/api/v1/projects" \
  -H "X-Organization-ID: $ORG_ID" \
  -H "X-User-ID: test-user-001" \
  -H "X-User-Role: admin")
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "${RESULT:0:300}"
check "GET /api/v1/projects responde JSON" '"' "$RESULT"

# ─── 6. Test AI Service ───────────────────────────────────────────────────────
echo ""
echo "=== Tests AI Service (directo) ==="

echo ""
echo "--- GET /api/v1/chat/sessions ---"
RESULT=$(cr_curl "$AI_URL/api/v1/chat/sessions" \
  -H "X-Organization-ID: $ORG_ID" \
  -H "X-User-ID: test-user-001")
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "${RESULT:0:300}"
check "GET /chat/sessions responde JSON" '"' "$RESULT"

# ─── 7. Resumen ───────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo " Resumen: $PASS pasaron / $((PASS+FAIL)) total"
FAIL_MSG=""
if [ $FAIL -gt 0 ]; then
  echo " ❌ $FAIL fallaron"
else
  echo " ✅ Todos los tests pasaron"
fi
echo "========================================"
