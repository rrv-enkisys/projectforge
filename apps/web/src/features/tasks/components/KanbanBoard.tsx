import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { Task } from '../hooks/useTasks'

const columns: { id: Task['status']; label: string; style: string; dot: string }[] = [
  { id: 'todo', label: 'To Do', style: 'bg-slate-50 border-slate-200', dot: 'bg-slate-400' },
  { id: 'in_progress', label: 'In Progress', style: 'bg-blue-50 border-blue-200', dot: 'bg-blue-500' },
  { id: 'done', label: 'Done', style: 'bg-green-50 border-green-200', dot: 'bg-green-500' },
]

const priorityColors: Record<Task['priority'], string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-slate-100 text-slate-600',
}

interface KanbanBoardProps {
  tasks: Task[]
  onEdit?: (task: Task) => void
}

export function KanbanBoard({ tasks, onEdit }: KanbanBoardProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {columns.map((col) => {
        const colTasks = tasks.filter((t) => t.status === col.id)
        return (
          <div key={col.id} className={cn('rounded-xl border p-3 min-h-[200px]', col.style)}>
            <div className="mb-3 flex items-center gap-2">
              <span className={cn('h-2 w-2 rounded-full', col.dot)} />
              <span className="text-sm font-semibold text-slate-700">{col.label}</span>
              <span className="ml-auto rounded-full bg-white border px-2 py-0.5 text-xs text-slate-500 font-medium">
                {colTasks.length}
              </span>
            </div>

            <div className="space-y-2">
              {colTasks.map((task) => (
                <Card
                  key={task.id}
                  className="cursor-pointer hover:shadow-md transition-all hover:-translate-y-0.5 bg-white"
                  onClick={() => onEdit?.(task)}
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
              ))}

              {colTasks.length === 0 && (
                <p className="py-6 text-center text-xs text-slate-400">No tasks</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
