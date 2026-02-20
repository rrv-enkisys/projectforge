import { useDroppable } from '@dnd-kit/core'
import { cn } from '@/lib/utils'
import type { Task } from '../hooks/useTasks'
import { KanbanCard } from './KanbanCard'

export interface KanbanColumnDef {
  id: Task['status']
  label: string
  style: string
  dot: string
  overStyle: string
}

interface KanbanColumnProps {
  column: KanbanColumnDef
  tasks: Task[]
  onEdit?: (task: Task) => void
}

export function KanbanColumn({ column, tasks, onEdit }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'rounded-xl border p-3 min-h-[200px] transition-colors',
        column.style,
        isOver && column.overStyle,
      )}
    >
      <div className="mb-3 flex items-center gap-2">
        <span className={cn('h-2 w-2 rounded-full', column.dot)} />
        <span className="text-sm font-semibold text-slate-700">{column.label}</span>
        <span className="ml-auto rounded-full bg-white border px-2 py-0.5 text-xs text-slate-500 font-medium">
          {tasks.length}
        </span>
      </div>

      <div className="space-y-2 min-h-[60px]">
        {tasks.map((task) => (
          <KanbanCard key={task.id} task={task} onEdit={onEdit} />
        ))}

        {tasks.length === 0 && (
          <p className="py-6 text-center text-xs text-slate-400">No tasks</p>
        )}
      </div>
    </div>
  )
}
