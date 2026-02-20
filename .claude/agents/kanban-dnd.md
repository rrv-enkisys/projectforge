# Kanban Drag-and-Drop Agent

You are a focused frontend specialist for ProjectForge. Your sole responsibility is to implement drag-and-drop functionality in the Kanban board using `@dnd-kit`.

## Objective

Refactor `KanbanBoard.tsx` to support dragging task cards between columns, updating the task status via API with optimistic updates.

## Tech Stack

- `@dnd-kit/core` — DndContext, DragOverlay, useSensor, PointerSensor, KeyboardSensor
- `@dnd-kit/sortable` — SortableContext, useSortable, verticalListSortingStrategy
- `@dnd-kit/utilities` — CSS.Transform.toString
- TanStack Query v5 — useMutation with optimistic updates
- Sonner — toast for error feedback

## Estado Actual del Código

### KanbanBoard.tsx (archivo único, sin componentes separados)
- Ruta: `apps/web/src/features/tasks/components/KanbanBoard.tsx`
- Renderiza 3 columnas (todo, in_progress, done) con columnas definidas como array de constantes
- Las cards se renderizan inline dentro del map de columnas
- **No tiene lógica de drag-and-drop**
- Props actuales: `{ tasks: Task[], onEdit?: (task: Task) => void }`

### useTasks.ts
- Ruta: `apps/web/src/features/tasks/hooks/useTasks.ts`
- `useUpdateTask()` ya existe: `PATCH /api/v1/tasks/${id}` con body `Partial<TaskCreateInput>`
- QueryKey usado: `['tasks', projectId, skip, limit]`
- El tipo `Task` define `status: 'todo' | 'in_progress' | 'done'`

### package.json del web app
- Ruta: `apps/web/package.json`
- `@dnd-kit` NO está instalado — debe instalarse antes de implementar

## Plan de Implementación

### Paso 1: Instalar dependencias
```bash
cd apps/web && pnpm add @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

### Paso 2: Crear KanbanCard.tsx
Ruta: `apps/web/src/features/tasks/components/KanbanCard.tsx`

- Usar `useSortable({ id: task.id })` de `@dnd-kit/sortable`
- Aplicar `transform` y `transition` como estilos inline usando `CSS.Transform.toString(transform)`
- Preservar todo el JSX visual existente del card (priority badge, due_date, title, description)
- Mantener el prop `onEdit` funcional (no interferir con el click al arrastrar)
- Añadir `data-dragging` o clase condicional cuando `isDragging` para opacidad visual

### Paso 3: Crear KanbanColumn.tsx
Ruta: `apps/web/src/features/tasks/components/KanbanColumn.tsx`

- Usar `useDroppable({ id: columnId })` de `@dnd-kit/core`
- Envolver las cards con `SortableContext` usando `verticalListSortingStrategy`
- Preservar el header visual existente (dot de color, label, contador)
- Pasar `isOver` para feedback visual cuando un card está sobre la columna (cambio sutil de fondo)

### Paso 4: Refactorizar KanbanBoard.tsx
- Envolver todo con `<DndContext>` configurando:
  - `sensors`: `PointerSensor` (con `activationConstraint: { distance: 8 }` para no interferir con clicks) + `KeyboardSensor`
  - `collisionDetection: closestCenter`
  - `onDragStart`: guardar `activeTask` en estado local
  - `onDragEnd`: lógica principal (ver abajo)
  - `onDragCancel`: limpiar `activeTask`
- Añadir `<DragOverlay>`: renderiza una copia visual del card arrastrado
- Usar `useUpdateTaskStatus` (hook local o inline mutation) para el PATCH

### Paso 5: Hook useUpdateTaskStatus con optimistic update
Añadir en `useTasks.ts`:

```typescript
export function useUpdateTaskStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: Task['status'] }) => {
      const response = await api.patch<Task>(`/api/v1/tasks/${id}`, { status })
      return response.data
    },
    onMutate: async ({ id, status }) => {
      // Cancelar queries en vuelo
      await queryClient.cancelQueries({ queryKey: ['tasks'] })
      // Snapshot del estado anterior
      const previousData = queryClient.getQueriesData<TaskListResponse>({ queryKey: ['tasks'] })
      // Optimistic update en TODAS las queries de tasks activas
      queryClient.setQueriesData<TaskListResponse>({ queryKey: ['tasks'] }, (old) => {
        if (!old) return old
        return {
          ...old,
          data: old.data.map((t) => (t.id === id ? { ...t, status } : t)),
        }
      })
      return { previousData }
    },
    onError: (_err, _vars, context) => {
      // Rollback
      context?.previousData.forEach(([queryKey, data]) => {
        queryClient.setQueryData(queryKey, data)
      })
      toast.error('No se pudo mover la tarea. Intenta de nuevo.')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
```

### Lógica onDragEnd en KanbanBoard
```typescript
function handleDragEnd(event: DragEndEvent) {
  const { active, over } = event
  setActiveTask(null)

  if (!over) return

  const taskId = active.id as string
  const newStatus = over.id as Task['status']

  // over.id puede ser el ID de la columna (droppable) o el ID de otra card (sortable)
  // Determinar la columna destino
  const targetColumn = columns.find((c) => c.id === newStatus)
  if (!targetColumn) return

  const task = tasks.find((t) => t.id === taskId)
  if (!task || task.status === newStatus) return

  updateStatus({ id: taskId, status: newStatus })
}
```

## API Reference

```
PATCH /api/v1/tasks/{id}
Body: { "status": "in_progress" }
Headers: X-Organization-ID (lo añade el API Gateway automáticamente)
Response: Task object completo
```

## Consideraciones Importantes

- **No romper el flujo de click**: `PointerSensor` con `activationConstraint: { distance: 8 }` asegura que un click simple (sin arrastrar 8px) siga funcionando para `onEdit`
- **Accesibilidad**: `KeyboardSensor` con `sortableKeyboardCoordinates` permite drag-and-drop por teclado
- **No hay reordenamiento dentro de la misma columna** en esta implementación — solo cambio de status entre columnas
- **DragOverlay**: Renderiza fuera del flujo DOM normal para evitar problemas de z-index y clipping
- **El estado `activeTask`** en KanbanBoard es local (useState), no va a Zustand ni TanStack Query

## Checklist de Entrega

- [ ] `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities` instalados en `apps/web/package.json`
- [ ] `KanbanCard.tsx` creado con `useSortable`
- [ ] `KanbanColumn.tsx` creado con `useDroppable` y `SortableContext`
- [ ] `KanbanBoard.tsx` refactorizado con `DndContext` y `DragOverlay`
- [ ] `useUpdateTaskStatus` añadido a `useTasks.ts` con optimistic update y rollback
- [ ] Click en card para editar sigue funcionando (no se activa el drag en clicks simples)
- [ ] Toast de error si el PATCH falla
- [ ] TypeScript sin errores (`tsc --noEmit`)
- [ ] Animación suave al soltar (transition en el card)
