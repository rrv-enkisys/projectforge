import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { Task } from '../hooks/useTasks'

export const priorityColors: Record<Task['priority'], string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-slate-100 text-slate-600',
}

interface KanbanCardProps {
  task: Task
  onEdit?: (task: Task) => void
}

export function KanbanCard({ task, onEdit }: KanbanCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: task.id,
    data: { task },
  })

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <Card
        className={cn(
          'cursor-grab bg-white transition-all',
          isDragging
            ? 'opacity-40 shadow-none'
            : 'hover:shadow-md hover:-translate-y-0.5',
        )}
        onClick={() => onEdit?.(task)}
        {...listeners}
      >
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
    </div>
  )
}
