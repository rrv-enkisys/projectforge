import { useState } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { Task } from '../hooks/useTasks'
import { useUpdateTaskStatus } from '../hooks/useTasks'
import { KanbanColumn, type KanbanColumnDef } from './KanbanColumn'
import { priorityColors } from './KanbanCard'

const columns: KanbanColumnDef[] = [
  {
    id: 'todo',
    label: 'To Do',
    style: 'bg-slate-50 border-slate-200',
    dot: 'bg-slate-400',
    overStyle: 'border-slate-400 bg-slate-100',
  },
  {
    id: 'in_progress',
    label: 'In Progress',
    style: 'bg-blue-50 border-blue-200',
    dot: 'bg-blue-500',
    overStyle: 'border-blue-400 bg-blue-100',
  },
  {
    id: 'done',
    label: 'Done',
    style: 'bg-green-50 border-green-200',
    dot: 'bg-green-500',
    overStyle: 'border-green-400 bg-green-100',
  },
]

interface KanbanBoardProps {
  tasks: Task[]
  onEdit?: (task: Task) => void
}

export function KanbanBoard({ tasks, onEdit }: KanbanBoardProps) {
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const updateStatus = useUpdateTaskStatus()

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
  )

  function handleDragStart(event: DragStartEvent) {
    const task = tasks.find((t) => t.id === event.active.id)
    setActiveTask(task ?? null)
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    setActiveTask(null)

    if (!over) return

    const taskId = active.id as string
    const newStatus = over.id as Task['status']

    if (!columns.find((c) => c.id === newStatus)) return

    const task = tasks.find((t) => t.id === taskId)
    if (!task || task.status === newStatus) return

    updateStatus.mutate({ id: taskId, status: newStatus })
  }

  function handleDragCancel() {
    setActiveTask(null)
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {columns.map((col) => (
          <KanbanColumn
            key={col.id}
            column={col}
            tasks={tasks.filter((t) => t.status === col.id)}
            onEdit={onEdit}
          />
        ))}
      </div>

      <DragOverlay>
        {activeTask && <OverlayCard task={activeTask} />}
      </DragOverlay>
    </DndContext>
  )
}

function OverlayCard({ task }: { task: Task }) {
  return (
    <Card className="cursor-grabbing shadow-xl bg-white rotate-1">
      <CardContent className="p-3 space-y-2">
        <p className="text-sm font-medium text-slate-900 leading-snug">{task.title}</p>
        {task.description && (
          <p className="text-xs text-slate-500 line-clamp-2">{task.description}</p>
        )}
        <div className="flex items-center justify-between gap-2">
          <span
            className={cn(
              'rounded-full px-2 py-0.5 text-xs font-semibold capitalize',
              priorityColors[task.priority],
            )}
          >
            {task.priority}
          </span>
          {task.due_date && (
            <span className="text-xs text-slate-400">
              {new Date(task.due_date).toLocaleDateString()}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
