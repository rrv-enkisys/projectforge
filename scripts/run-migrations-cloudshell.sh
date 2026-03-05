#!/bin/bash
# =============================================================================
# ProjectForge — Aplicar migraciones en Cloud SQL dev
# Ejecutar desde Cloud Shell (console.cloud.google.com) o VM con auth válida
# =============================================================================
set -euo pipefail

PROJECT_ID="projectforge-4314f"
INSTANCE_NAME="projectforge-dev"
DB_USER="postgres"
DB_NAME="projectforge"
REGION="us-central1"

echo "=== ProjectForge — Aplicando migraciones ==="
echo "Proyecto:  $PROJECT_ID"
echo "Instancia: $INSTANCE_NAME"
echo "Usuario:   $DB_USER / DB: $DB_NAME"
echo ""

# Verificar que la instancia existe y está RUNNABLE
STATUS=$(gcloud sql instances describe "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --format="value(state)" 2>&1)
if [ "$STATUS" != "RUNNABLE" ]; then
  echo "ERROR: Cloud SQL instance state: $STATUS (expected RUNNABLE)"
  exit 1
fi
echo "✓ Cloud SQL instance RUNNABLE"

# Password (desde Secret Manager)
DB_PASS=$(gcloud secrets versions access latest \
  --secret="cloud-sql-password-dev" \
  --project="$PROJECT_ID")
echo "✓ Password obtenida desde Secret Manager"

# ─── Instalar migrate CLI si no está disponible ───────────────────────────
if ! command -v migrate &>/dev/null; then
  echo "Instalando golang-migrate..."
  curl -sL https://github.com/golang-migrate/migrate/releases/download/v4.17.0/migrate.linux-amd64.tar.gz \
    | tar -xz -C /tmp migrate
  chmod +x /tmp/migrate
  export PATH="/tmp:$PATH"
  echo "✓ golang-migrate instalado: $(migrate --version)"
fi

# ─── Arrancar Cloud SQL Auth Proxy ────────────────────────────────────────
PROXY_BIN=""
if command -v cloud_sql_proxy &>/dev/null; then
  PROXY_BIN="cloud_sql_proxy"
elif command -v cloud-sql-proxy &>/dev/null; then
  PROXY_BIN="cloud-sql-proxy"
else
  echo "Descargando Cloud SQL Auth Proxy v2..."
  curl -sLo /tmp/cloud-sql-proxy \
    "https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.1/cloud-sql-proxy.linux.amd64"
  chmod +x /tmp/cloud-sql-proxy
  PROXY_BIN="/tmp/cloud-sql-proxy"
fi

$PROXY_BIN --port=5433 \
  "$PROJECT_ID:$REGION:$INSTANCE_NAME" \
  &>/tmp/proxy-migrate.log &
PROXY_PID=$!
echo "Cloud SQL Proxy PID: $PROXY_PID"
sleep 5

if ! pg_isready -h 127.0.0.1 -p 5433 -q 2>/dev/null; then
  echo "ERROR: Proxy no respondió. Log:"
  cat /tmp/proxy-migrate.log
  exit 1
fi
echo "✓ Proxy listo en 127.0.0.1:5433"

# Cleanup al salir
trap "kill $PROXY_PID 2>/dev/null; echo 'Proxy detenido'" EXIT

# ─── Crear la base de datos si no existe ──────────────────────────────────
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d postgres \
  -c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" | grep -q 1 || \
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d postgres \
  -c "CREATE DATABASE $DB_NAME;"
echo "✓ Base de datos '$DB_NAME' disponible"

# ─── Habilitar pgvector ────────────────────────────────────────────────────
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
  -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1 | grep -v "^$"
echo "✓ Extensión pgvector habilitada"

# ─── Aplicar migraciones con golang-migrate ────────────────────────────────
MIGRATIONS_DIR="/home/clave-vm-20260210/projectforge/migrations"
# En Cloud Shell, clonar el repo primero si no hay acceso local:
if [ ! -d "$MIGRATIONS_DIR" ]; then
  MIGRATIONS_DIR="$(pwd)/migrations"
  if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "ERROR: No se encuentran los archivos de migración en $MIGRATIONS_DIR"
    echo "Clona el repo primero: git clone git@github.com:rrv-enkisys/projectforge.git"
    exit 1
  fi
fi

DATABASE_URL="postgres://$DB_USER:$DB_PASS@127.0.0.1:5433/$DB_NAME?sslmode=disable"

echo ""
echo "=== Ejecutando migraciones ==="
migrate \
  -source "file://$MIGRATIONS_DIR" \
  -database "$DATABASE_URL" \
  up

echo ""
echo "=== Estado de migraciones ==="
migrate \
  -source "file://$MIGRATIONS_DIR" \
  -database "$DATABASE_URL" \
  version

echo ""
echo "=== Verificando tablas creadas ==="
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
  -c "\dt" 2>&1

echo ""
echo "=== Verificando pgvector ==="
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
  -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" 2>&1

echo ""
echo "✅ Migraciones completadas exitosamente"
