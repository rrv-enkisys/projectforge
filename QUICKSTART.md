# ProjectForge Quick Start Guide

## 🎯 Objetivo
Ver el proyecto funcionando en la VM y acceder desde tu navegador.

## 📍 Información de tu VM
- **IP Externa**: `34.45.186.91`
- **Usuario**: `clave-vm-20260210`
- **Proyecto**: `/home/clave-vm-20260210/projectforge`

## 🚀 Opción 1: Instalación Automática (Recomendado)

### Paso 1: Instalar Dependencias
```bash
cd ~/projectforge
./setup-vm.sh
```

Después de la instalación, **es importante** recargar el shell:
```bash
source ~/.bashrc
newgrp docker
```

### Paso 2: Iniciar Servicios Base
```bash
cd ~/projectforge
./start-dev.sh
```

Esto iniciará PostgreSQL y Redis en Docker y aplicará las migraciones.

### Paso 3: Iniciar Servicios de Aplicación

**Opción A: Usando tmux (Recomendado)**
```bash
# Instalar tmux si no está
sudo apt-get install -y tmux

# Crear sesión con ventanas múltiples
cd ~/projectforge
tmux new-session -d -s projectforge

# Core Service (ventana 0)
tmux send-keys -t projectforge:0 'cd ~/projectforge/apps/core-service && poetry install && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload' C-m

# AI Service (ventana 1)
tmux new-window -t projectforge:1
tmux send-keys -t projectforge:1 'cd ~/projectforge/apps/ai-service && poetry install && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload' C-m

# API Gateway (ventana 2)
tmux new-window -t projectforge:2
tmux send-keys -t projectforge:2 'cd ~/projectforge/apps/api-gateway && go mod download && go run cmd/server/main.go' C-m

# Frontend (ventana 3)
tmux new-window -t projectforge:3
tmux send-keys -t projectforge:3 'cd ~/projectforge/apps/web && pnpm install && pnpm dev --host 0.0.0.0' C-m

# Adjuntar a la sesión
tmux attach -t projectforge
```

**Navegar en tmux:**
- `Ctrl+B` luego `0`/`1`/`2`/`3` - Cambiar entre ventanas
- `Ctrl+B` luego `d` - Detach (servicios siguen corriendo)
- `tmux attach -t projectforge` - Re-attach
- `Ctrl+B` luego `x` - Cerrar ventana actual

**Opción B: Terminales Separadas**

Terminal 1 - Core Service:
```bash
cd ~/projectforge/apps/core-service
poetry install
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - AI Service:
```bash
cd ~/projectforge/apps/ai-service
poetry install
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

Terminal 3 - API Gateway:
```bash
cd ~/projectforge/apps/api-gateway
go mod download
go run cmd/server/main.go
```

Terminal 4 - Frontend:
```bash
cd ~/projectforge/apps/web
pnpm install
pnpm dev --host 0.0.0.0
```

### Paso 4: Abrir Firewall (Importante para GCP)

```bash
# Permitir tráfico en los puertos necesarios
gcloud compute firewall-rules create projectforge-dev \
    --allow tcp:5173,tcp:8080,tcp:8000,tcp:8001 \
    --source-ranges 0.0.0.0/0 \
    --description "ProjectForge development ports"
```

O desde la consola de GCP:
1. Ve a VPC Network > Firewall
2. Create Firewall Rule
3. Nombre: `projectforge-dev`
4. Targets: All instances
5. Source IP ranges: `0.0.0.0/0`
6. Protocols and ports: tcp: `5173,8080,8000,8001`

### Paso 5: Acceder desde tu Navegador

Una vez que todos los servicios estén corriendo:

🌐 **URLs de Acceso:**
- **Frontend (React)**: http://34.45.186.91:5173
- **API Gateway**: http://34.45.186.91:8080
- **Core Service Docs**: http://34.45.186.91:8000/docs
- **AI Service Docs**: http://34.45.186.91:8001/docs

## 🎨 Opción 2: Solo Ver la Documentación

Si solo quieres explorar el código sin ejecutar:

```bash
cd ~/projectforge

# Ver estructura del proyecto
tree -L 2 -I 'node_modules|dist|__pycache__'

# Ver documentación de arquitectura
cat ARCHITECTURE.md

# Ver READMEs de cada servicio
cat apps/core-service/README.md
cat apps/ai-service/README.md
cat apps/api-gateway/README.md
cat apps/web/README.md
```

## 🐛 Solución de Problemas

### Error: "Cannot connect to Docker daemon"
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

### Error: "poetry: command not found"
```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

### Error: "go: command not found"
```bash
export PATH="$PATH:/usr/local/go/bin"
source ~/.bashrc
```

### Error: "pnpm: command not found"
```bash
export PNPM_HOME="$HOME/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"
source ~/.bashrc
```

### Puerto en uso
```bash
# Ver qué está usando el puerto
sudo lsof -i :8080

# Matar proceso si es necesario
sudo kill -9 <PID>
```

### Ver logs de Docker
```bash
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Reiniciar servicios Docker
```bash
docker-compose down
docker-compose up -d postgres redis
```

## 📊 Verificar Estado de Servicios

```bash
# Docker services
docker ps

# Health checks
curl http://localhost:8000/health  # Core Service
curl http://localhost:8001/health  # AI Service
curl http://localhost:8080/health  # API Gateway

# PostgreSQL
docker exec -it projectforge-postgres psql -U postgres -d projectforge -c "\dt"

# Redis
docker exec -it projectforge-redis redis-cli ping
```

## 🛑 Detener Todo

```bash
# Detener servicios de aplicación (Ctrl+C en cada terminal o tmux)

# Detener Docker
cd ~/projectforge
docker-compose down

# Detener y limpiar todo
docker-compose down -v  # ⚠️ Esto borra los datos de la BD
```

## 🔐 Configuración de Firebase (Requerido para Auth)

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Crea un proyecto o selecciona uno existente
3. Ve a Project Settings > General
4. Copia las credenciales de Firebase Config

5. Edita el archivo `.env`:
```bash
nano ~/projectforge/.env
```

Actualiza estas variables:
```bash
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

6. Edita también `apps/web/.env`:
```bash
cp apps/web/.env.example apps/web/.env
nano apps/web/.env
```

## 📝 Notas

- **Desarrollo**: Los servicios usan `--reload` para recarga automática
- **Puertos**: Asegúrate de que los puertos 5173, 8000, 8001, 8080, 5432, 6379 estén disponibles
- **RAM**: El proyecto puede consumir ~2GB de RAM con todos los servicios
- **Primera Vez**: La instalación de dependencias puede tomar 5-10 minutos

## 🆘 ¿Necesitas Ayuda?

Si encuentras algún error:
1. Verifica los logs de cada servicio
2. Asegúrate de que PostgreSQL esté corriendo
3. Verifica que los puertos no estén en uso
4. Revisa que las variables de entorno estén configuradas

## 📚 Documentación Adicional

- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura del sistema
- [README.md](README.md) - Documentación general
- [apps/core-service/README.md](apps/core-service/README.md) - Core Service
- [apps/ai-service/README.md](apps/ai-service/README.md) - AI Service
- [apps/api-gateway/README.md](apps/api-gateway/README.md) - API Gateway
- [apps/web/README.md](apps/web/README.md) - Frontend
