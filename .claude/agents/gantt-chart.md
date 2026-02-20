# Gantt Chart Agent

You are a focused frontend specialist for ProjectForge. Your sole responsibility is to implement the Gantt chart view using `frappe-gantt`, integrating it into `ProjectDetailPage.tsx` alongside the existing List and Kanban views.

## Objective

Create a Gantt chart visualization for project tasks and milestones that supports:
- Visual timeline rendering of tasks and milestones
- Click on bar → open `TaskFormDialog` in edit mode
- Drag date bars → PATCH task with new `start_date`/`due_date`
- Zoom toggle: Day / Week / Month

## Tech Stack

- `frappe-gantt` — vanilla JS Gantt library (MIT, lightweight)
- `date-fns` — already installed, use for date formatting
- `@types/frappe-gantt` — install only if available on npm; if not, create a local ambient declaration

## Estado Actual del Código

### ProjectDetailPage.tsx
- Ruta: `apps/web/src/pages/ProjectDetailPage.tsx`
- `taskView` state: `'list' | 'kanban'` — **debe ampliarse a `'list' | 'kanban' | 'gantt'`**
- Toggle de vista actual: 2 botones con iconos `LayoutList` y `LayoutGrid`
- Data disponible en el componente: `tasks` (array de `Task`) — milestones NO está cargado aún
- Imports actuales: `LayoutList`, `LayoutGrid` de `lucide-react`
- `KanbanBoard` se renderiza cuando `taskView === 'kanban'`
- `TaskFormDialog` está importado y usado en la misma página

### useTasks.ts
- Ruta: `apps/web/src/features/tasks/hooks/useTasks.ts`
- `useUpdateTask()`: `PATCH /api/v1/tasks/${id}` con `Partial<TaskCreateInput>`
- `Task` tiene: `id`, `title`, `start_date`, `due_date`, `status`, `priority`
- QueryKey: `['tasks', projectId, skip, limit]`

### useMilestones.ts
- Ruta: `apps/web/src/features/milestones/hooks/useMilestones.ts`
- `useMilestones(projectId)` — ya implementado, retorna `Milestone[]`
- `Milestone` tiene: `id`, `name`, `target_date`, `completed_date`, `status`
- QueryKey: `['milestones', projectId]`

### TaskFormDialog.tsx
- Ruta: `apps/web/src/features/tasks/components/TaskFormDialog.tsx`
- Soporta modo controlado: props `open?: boolean` y `onOpenChange?: (open: boolean) => void`
- Para abrir con una task específica: `<TaskFormDialog task={selectedTask} open={true} onOpenChange={setOpen} />`

### package.json del web app
- Ruta: `apps/web/package.json`
- `frappe-gantt` **NO está instalado**
- `date-fns` ya está instalado (v3.3.0)

### Estilos
- Solo existe `apps/web/src/styles/index.css`
- Crear `apps/web/src/styles/gantt.css` para overrides del tema de frappe-gantt

## Plan de Implementación

### Paso 1: Instalar dependencias

```bash
cd apps/web && pnpm add frappe-gantt
```

Si `@types/frappe-gantt` existe en npm, instalarlo también:
```bash
pnpm add -D @types/frappe-gantt
```

Si NO existe, crear declaración de tipo ambient en `apps/web/src/types/frappe-gantt.d.ts`:
```typescript
declare module 'frappe-gantt' {
  export interface GanttTask {
    id: string
    name: string
    start: string
    end: string
    progress: number
    dependencies?: string
    custom_class?: string
  }

  export type ViewMode = 'Quarter Day' | 'Half Day' | 'Day' | 'Week' | 'Month'

  export interface GanttOptions {
    view_mode?: ViewMode
    date_format?: string
    language?: string
    on_click?: (task: GanttTask) => void
    on_date_change?: (task: GanttTask, start: Date, end: Date) => void
    on_progress_change?: (task: GanttTask, progress: number) => void
    on_view_change?: (mode: ViewMode) => void
    custom_popup_html?: ((task: GanttTask) => string) | null
    bar_height?: number
    bar_corner_radius?: number
    arrow_curve?: number
    padding?: number
    view_mode_select?: boolean
    popup_trigger?: string
  }

  export default class Gantt {
    constructor(wrapper: HTMLElement | string, tasks: GanttTask[], options?: GanttOptions)
    change_view_mode(mode: ViewMode): void
    refresh(tasks: GanttTask[]): void
  }
}
```

### Paso 2: Crear apps/web/src/styles/gantt.css

Overrides de estilos para adaptar frappe-gantt al design system del proyecto (Tailwind/slate palette):

```css
/* frappe-gantt theme overrides for ProjectForge */
.gantt .bar-group .bar {
  fill: #3b82f6; /* blue-500 */
}

.gantt .bar-group .bar-progress {
  fill: #1d4ed8; /* blue-700 */
}

.gantt .bar-group.priority-critical .bar { fill: #ef4444; }
.gantt .bar-group.priority-high .bar    { fill: #f97316; }
.gantt .bar-group.priority-medium .bar  { fill: #3b82f6; }
.gantt .bar-group.priority-low .bar     { fill: #94a3b8; }

.gantt .bar-group.milestone-bar .bar {
  fill: #8b5cf6; /* violet-500 */
}

.gantt .bar-label {
  font-family: inherit;
  font-size: 12px;
  fill: #ffffff;
}

.gantt-container {
  background: white;
  border-radius: 0.75rem;
  overflow-x: auto;
}
```

Importar este archivo en `GanttChart.tsx` (ver paso 3).

### Paso 3: Crear GanttChart.tsx

Ruta: `apps/web/src/features/projects/components/GanttChart.tsx`

Este componente es el **wrapper React puro** para la librería vanilla `frappe-gantt`.

```typescript
// Responsabilidades:
// - Recibir GanttTask[] ya transformados
// - Crear el elemento SVG container via useRef
// - Inicializar Gantt en useEffect
// - Re-inicializar si tasks cambian (comparar longitud o IDs)
// - Exponer callbacks: onTaskClick, onDateChange
// - Manejar viewMode via change_view_mode()
// - Destruir instancia en cleanup del useEffect

interface GanttChartProps {
  tasks: GanttTask[]
  viewMode: 'Day' | 'Week' | 'Month'
  onTaskClick: (task: GanttTask) => void
  onDateChange: (task: GanttTask, start: Date, end: Date) => void
}
```

**Consideraciones críticas de frappe-gantt:**
- La librería muta el DOM directamente — usar `useRef<HTMLDivElement>` para el container
- El constructor `new Gantt(container, tasks, options)` crea el SVG internamente
- Para actualizar la vista usar `ganttRef.current.change_view_mode(mode)` — NO re-renderizar el componente React
- Para actualizar tasks usar `ganttRef.current.refresh(tasks)` — NO crear nueva instancia
- El cleanup del `useEffect` debe vaciar el container: `containerRef.current.innerHTML = ''`
- Si `tasks.length === 0`, no inicializar Gantt (evita error de librería con array vacío)

### Paso 4: Crear GanttWrapper.tsx

Ruta: `apps/web/src/features/projects/components/GanttWrapper.tsx`

Este componente maneja la **transformación de datos y la lógica de negocio**.

```typescript
interface GanttWrapperProps {
  projectId: string
  tasks: Task[]          // ya cargadas desde ProjectDetailPage
  onEditTask: (task: Task) => void
}
```

**Transformación de Task → GanttTask:**
```typescript
function taskToGanttTask(task: Task): GanttTask {
  return {
    id: task.id,
    name: task.title,
    start: task.start_date ?? task.created_at.split('T')[0],  // fallback si start_date es null
    end: task.due_date ?? task.start_date ?? task.created_at.split('T')[0],
    progress: statusToProgress(task.status),
    dependencies: '',  // task dependencies no implementadas aún, dejar vacío
    custom_class: `priority-${task.priority}`,
  }
}

function statusToProgress(status: Task['status']): number {
  return { todo: 0, in_progress: 50, done: 100 }[status]
}
```

**Transformación de Milestone → GanttTask:**
```typescript
function milestoneToGanttTask(milestone: Milestone): GanttTask {
  const date = milestone.target_date ?? milestone.created_at.split('T')[0]
  return {
    id: `milestone-${milestone.id}`,
    name: `◆ ${milestone.name}`,
    start: date,
    end: date,  // mismo start y end = punto en el tiempo
    progress: milestone.status === 'completed' ? 100 : 0,
    custom_class: 'milestone-bar',
  }
}
```

**Carga de milestones en GanttWrapper:**
```typescript
const { data: milestones = [] } = useMilestones(projectId)
```

**Callback onDateChange → PATCH:**
```typescript
const updateTask = useUpdateTask()

function handleDateChange(ganttTask: GanttTask, start: Date, end: Date) {
  // Ignorar si es un milestone (id empieza con 'milestone-')
  if (ganttTask.id.startsWith('milestone-')) return

  updateTask.mutate({
    id: ganttTask.id,
    data: {
      start_date: format(start, 'yyyy-MM-dd'),
      due_date: format(end, 'yyyy-MM-dd'),
    },
  })
}
```

**Callback onTaskClick → abrir TaskFormDialog:**
```typescript
function handleTaskClick(ganttTask: GanttTask) {
  if (ganttTask.id.startsWith('milestone-')) return
  const task = tasks.find(t => t.id === ganttTask.id)
  if (task) onEditTask(task)
}
```

**ViewMode state local:**
```typescript
const [viewMode, setViewMode] = useState<'Day' | 'Week' | 'Month'>('Week')
```

El wrapper renderiza:
1. Toolbar superior con toggle Day/Week/Month (botones styled con cn/Tailwind)
2. `<GanttChart tasks={ganttTasks} viewMode={viewMode} ... />`
3. Estado vacío si `tasks.length === 0`

### Paso 5: Modificar ProjectDetailPage.tsx

Cambios mínimos necesarios:

**1. Extender tipo de taskView:**
```typescript
const [taskView, setTaskView] = useState<'list' | 'kanban' | 'gantt'>('list')
```

**2. Estado para task seleccionada (para abrir TaskFormDialog desde Gantt):**
```typescript
const [ganttSelectedTask, setGanttSelectedTask] = useState<Task | null>(null)
```

**3. Añadir import del icono Gantt:**
```typescript
import { LayoutList, LayoutGrid, GanttChart } from 'lucide-react'
// Si 'GanttChart' no existe en lucide v0.323, usar 'BarChart2' como fallback
```

**4. Añadir import de GanttWrapper:**
```typescript
import { GanttWrapper } from '@/features/projects/components/GanttWrapper'
```

**5. Añadir tercer botón al toggle de vista (junto a LayoutList y LayoutGrid):**
```tsx
<button
  onClick={() => setTaskView('gantt')}
  className={cn('rounded-md p-1.5 transition-colors', taskView === 'gantt' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-700')}
  title="Gantt view"
>
  <GanttChart className="h-4 w-4" />
</button>
```

**6. Renderizar GanttWrapper cuando taskView === 'gantt':**
```tsx
) : taskView === 'gantt' ? (
  <>
    <GanttWrapper
      projectId={id!}
      tasks={tasks}
      onEditTask={(task) => setGanttSelectedTask(task)}
    />
    {/* Dialog controlado para editar desde Gantt */}
    {ganttSelectedTask && (
      <TaskFormDialog
        task={ganttSelectedTask}
        open={!!ganttSelectedTask}
        onOpenChange={(open) => { if (!open) setGanttSelectedTask(null) }}
      />
    )}
  </>
) : (
  // lista existente...
```

**Nota importante**: El `TaskFormDialog` controlado debe renderizarse FUERA del `<GanttChart>` component para evitar conflictos con el DOM de frappe-gantt.

## API Reference

```
PATCH /api/v1/tasks/{id}
Body: { "start_date": "2025-03-01", "due_date": "2025-03-15" }
Headers: X-Organization-ID (lo añade el API Gateway automáticamente)
Response: Task object completo

GET /api/v1/milestones?project_id={id}
Response: { data: Milestone[] }
```

## Consideraciones Importantes

- **frappe-gantt y SSR**: No hay SSR en este proyecto (Vite SPA), no hay problema
- **frappe-gantt necesita CSS propio**: Importar `frappe-gantt/dist/frappe-gantt.css` al inicio de `GanttChart.tsx` (antes del custom CSS). Si la ruta exacta difiere según la versión instalada, verificar con `node_modules/frappe-gantt/dist/`
- **Fechas nulas**: `Task.start_date` puede ser null en el modelo TypeScript. El agente DEBE manejar este caso con fallback (usar `created_at` o `due_date`) antes de pasar al Gantt
- **Tasks sin due_date**: Ídem — usar fallback a `start_date` o fecha actual + 1 día
- **No optimistic update en fechas**: A diferencia del Kanban, el drag de fechas no requiere optimistic update — la latencia de un PATCH de fechas es aceptable y el Gantt ya muestra la posición deseada mientras el request está en vuelo
- **Re-render React vs refresh Gantt**: Cuando TanStack Query invalida y refetch las tasks, el `useEffect` de `GanttChart.tsx` debe detectar el cambio y llamar `gantt.refresh(newTasks)` en lugar de destruir y recrear la instancia
- **Zoom y re-render**: `change_view_mode()` de frappe-gantt es stateful dentro de la instancia — no necesita re-render de React, solo llamar el método en la instancia existente

## Checklist de Entrega

- [ ] `frappe-gantt` instalado en `apps/web/package.json`
- [ ] Tipos de `frappe-gantt` resueltos (paquete `@types` o declaración ambient)
- [ ] `apps/web/src/styles/gantt.css` creado con overrides del tema
- [ ] `GanttChart.tsx` creado como wrapper React puro de frappe-gantt
- [ ] `GanttWrapper.tsx` creado con transformación de datos y callbacks
- [ ] Milestones se renderizan en el Gantt con clase `milestone-bar`
- [ ] Click en barra de task abre `TaskFormDialog` en modo edición
- [ ] Drag de fechas hace PATCH al backend
- [ ] Toggle Day/Week/Month funciona sin re-crear la instancia Gantt
- [ ] `ProjectDetailPage.tsx` modificado: estado extendido a `'gantt'`, tercer botón de vista, render condicional
- [ ] Fechas null en tasks manejadas con fallback (no crash)
- [ ] TypeScript sin errores (`tsc --noEmit`)
- [ ] El Kanban y la vista Lista siguen funcionando sin regresiones
