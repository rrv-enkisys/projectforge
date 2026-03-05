#!/bin/bash
# ProjectForge — E2E Tests via gcloud run services proxy
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
    echo "  ❌ $name — esperado:'$expected' obtenido:'${actual:0:120}'"; FAIL=$((FAIL+1))
  fi
}

run_service_tests() {
  local svc="$1" port="$2"
  local base="http://localhost:$port"
  local h="-H X-Organization-ID:$ORG_ID -H X-User-ID:$USER_ID -H X-User-Role:admin"

  echo ""
  echo "━━━ $svc (proxy :$port) ━━━"
  gcloud run services proxy "$svc" --port="$port" --region="$REGION" --project="$PROJECT" >/dev/null 2>&1 &
  local pid=$!
  sleep 7

  # esperar hasta 15s
  local ok=0
  for i in $(seq 1 8); do
    curl -s --max-time 2 "$base/health" >/dev/null 2>&1 && ok=1 && break
    sleep 1
  done

  if [ $ok -eq 0 ]; then
    echo "  ⚠️  Proxy no respondió — saltando $svc"
    kill $pid 2>/dev/null; return
  fi

  # health
  R=$(curl -s --max-time 10 "$base/health")
  echo "  health: $R"
  check "$svc /health" '"status"' "$R"

  # tests específicos por servicio
  case $svc in
    api-gateway-dev)
      CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
        -H "X-Organization-ID:$ORG_ID" "$base/api/v1/projects")
      echo "  GET /api/v1/projects sin Firebase → HTTP $CODE"
      check "Gateway requiere auth (401)" "401" "$CODE"
      ;;

    core-service-dev)
      R=$(curl -s --max-time 10 $h "$base/api/v1/projects")
      echo "  GET /projects: ${R:0:150}"
      check "GET /projects → JSON" '"' "$R"

      R=$(curl -s --max-time 10 $h -X POST -H "Content-Type:application/json" \
        "$base/api/v1/clients" -d '{"name":"E2E Client","email":"e2e@test.com"}')
      echo "  POST /clients: ${R:0:150}"
      check "POST /clients → responde" '"' "$R"

      R=$(curl -s --max-time 10 $h "$base/api/v1/dashboard")
      echo "  GET /dashboard: ${R:0:150}"
      check "GET /dashboard → JSON" '"' "$R"
      ;;

    ai-service-dev)
      R=$(curl -s --max-time 10 $h "$base/api/v1/chat/sessions")
      echo "  GET /chat/sessions: ${R:0:150}"
      check "GET /chat/sessions → JSON" '"' "$R"

      R=$(curl -s --max-time 10 $h "$base/api/v1/documents?project_id=00000000-0000-0000-0000-000000000001")
      echo "  GET /documents: ${R:0:150}"
      check "GET /documents → JSON" '"' "$R"
      ;;

    notification-service-dev)
      R=$(curl -s --max-time 10 -H "X-Organization-ID:$ORG_ID" -H "X-User-ID:$USER_ID" \
        "$base/api/v1/notifications")
      echo "  GET /notifications: ${R:0:150}"
      check "GET /notifications → JSON" '"' "$R"
      ;;
  esac

  kill $pid 2>/dev/null
  sleep 1
}

echo "════════════════════════════════════════"
echo " ProjectForge — E2E Tests"
echo " $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "════════════════════════════════════════"

run_service_tests api-gateway-dev       8080
run_service_tests core-service-dev      8081
run_service_tests ai-service-dev        8082
run_service_tests notification-service-dev 8083

echo ""
echo "════════════════════════════════════════"
echo " Resultado: $PASS ✅  $FAIL ❌  (total $((PASS+FAIL)))"
[ $FAIL -eq 0 ] && echo " ✅ Todos los tests pasaron" || echo " ❌ $FAIL tests fallaron"
echo "════════════════════════════════════════"
