# ProjectForge Frontend - Configuración Actual

## 🎯 Estado del Sistema

**Fecha:** 2026-02-16
**Modo:** Desarrollo (Sin autenticación Firebase)

### Servicios Activos

| Servicio | Puerto | URL | Estado |
|----------|--------|-----|--------|
| Frontend | 3000 | http://34.45.186.91:3000 | ✅ Running |
| Core Service | 8000 | http://34.45.186.91:8000 | ✅ Running |
| AI Service | 8001 | http://34.45.186.91:8001 | ✅ Running |

## 📊 Datos de Prueba

### Organización
- **EnkiSys** (ID: 11111111-1111-1111-1111-111111111111)

### Usuario
- **ricardo@enkisys.net** (Ricardo Reyes)

### Datos Disponibles
- ✅ **5 Proyectos** con diferentes estados
- ✅ **3 Clientes** (TechCorp, Innovate Solutions, Global Enterprise)
- ✅ **10 Tareas** distribuidas en proyectos
- ✅ **8 Milestones** (visibles en detalles de proyecto)

## 🌐 URLs del Frontend

### Páginas Principales
```
http://34.45.186.91:3000/dashboard   # Dashboard principal
http://34.45.186.91:3000/projects    # Lista de proyectos (5)
http://34.45.186.91:3000/clients     # Lista de clientes (3)
http://34.45.186.91:3000/tasks       # Lista de tareas (10)
```

### APIs Disponibles
```
http://34.45.186.91:8000/api/v1/docs    # Core Service Swagger
http://34.45.186.91:8001/api/v1/docs    # AI Service Swagger
```

## 🔧 Cambios Realizados

### 1. Autenticación Desactivada (Desarrollo)

**Archivo:** `apps/web/src/components/ProtectedRoute.tsx`
```typescript
const DEV_MODE = import.meta.env.DEV || import.meta.env.MODE === 'development'

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  // Skip authentication in development mode
  if (DEV_MODE) {
    return <>{children}</>
  }
  // ... resto del código
}
```

**Archivo:** `apps/web/src/lib/api.ts`
```typescript
const DEV_MODE = import.meta.env.DEV || import.meta.env.MODE === 'development'

// Skip auth in development mode
if (DEV_MODE) {
  return config
}
```

### 2. CORS Configurado

**Archivo:** `apps/core-service/.env`
```bash
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://34.45.186.91:3000"]
DEBUG=true
```

### 3. Tasks Endpoint Mejorado

**Archivo:** `apps/core-service/src/tasks/router.py`
- ✅ `project_id` es ahora opcional
- ✅ Lista todas las tareas si no se especifica proyecto

**Archivo:** `apps/core-service/src/tasks/repository.py`
- ✅ Agregado método `list_all()` para listar todas las tareas

### 4. Páginas Nuevas Creadas

- ✅ `apps/web/src/pages/ClientsPage.tsx` - Lista de clientes con cards
- ✅ `apps/web/src/pages/TasksPage.tsx` - Lista de tareas con estados y prioridades

### 5. Rutas Agregadas

**Archivo:** `apps/web/src/App.tsx`
```typescript
<Route path="/clients" element={<ProtectedRoute><ClientsPage /></ProtectedRoute>} />
<Route path="/tasks" element={<ProtectedRoute><TasksPage /></ProtectedRoute>} />
```

### 6. Sidebar Actualizado

**Archivo:** `apps/web/src/components/layout/Sidebar.tsx`
- ✅ Agregado link a Tasks
- ✅ Todos los links principales disponibles

## 🔄 Reiniciar Servicios

### Backend
```bash
# Core Service
cd ~/projectforge/apps/core-service
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000

# AI Service
cd ~/projectforge/apps/ai-service
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### Frontend
```bash
cd ~/projectforge/apps/web
pnpm dev --host 0.0.0.0
```

## 🐛 Troubleshooting

### Frontend no muestra datos
1. Forzar recarga: `Ctrl+Shift+R` (Windows/Linux) o `Cmd+Shift+R` (Mac)
2. Abrir DevTools (F12) → Console → buscar errores
3. Verificar Network tab para ver llamadas API
4. Verificar que las APIs respondan:
   ```bash
   curl http://34.45.186.91:8000/api/v1/projects
   curl http://34.45.186.91:8000/api/v1/clients
   curl http://34.45.186.91:8000/api/v1/tasks
   ```

### CORS Errors
- Verificar que `CORS_ORIGINS` en `.env` incluya la IP externa
- Reiniciar Core Service después de cambiar `.env`

### Puerto en uso
```bash
# Encontrar y matar proceso
ps aux | grep uvicorn
kill <PID>

# O matar todos
pkill -f uvicorn
```

## 📝 Notas Importantes

⚠️ **Modo Desarrollo Activo:**
- La autenticación Firebase está desactivada
- CORS permite acceso desde IP externa
- Solo para desarrollo, NO para producción

⚠️ **Milestones:**
- No tienen página separada por diseño
- Se muestran dentro de cada proyecto individual
- Accede a `/projects/:id` para ver milestones del proyecto

⚠️ **Próximos Pasos:**
- Implementar formularios para crear proyectos, clientes y tareas
- Agregar página de detalle de proyecto con Gantt chart
- Configurar Firebase Auth para producción
- Implementar funcionalidad de AI/RAG

## 🔒 Volver a Producción

Cuando estés listo para producción:

1. **Activar autenticación:**
   - Remover el bypass en `ProtectedRoute.tsx`
   - Remover el DEV_MODE check en `api.ts`

2. **Configurar CORS correcto:**
   - Solo dominios de producción en `CORS_ORIGINS`

3. **Cambiar DEBUG:**
   ```bash
   DEBUG=false
   ENVIRONMENT=production
   ```

---

**Documentación generada:** 2026-02-16
**Usuario:** ricardo@enkisys.net
**Proyecto:** ProjectForge v0.1.0
