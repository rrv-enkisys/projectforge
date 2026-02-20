import { useState } from 'react'
import { format } from 'date-fns'
import type { GanttTask, ViewMode } from 'frappe-gantt'
import { cn } from '@/lib/utils'
import type { Task } from '@/features/tasks/hooks/useTasks'
import { useUpdateTask } from '@/features/tasks/hooks/useTasks'
import { useMilestones } from '@/features/milestones/hooks/useMilestones'
import type { Milestone } from '@/features/milestones/hooks/useMilestones'
import { GanttChart } from './GanttChart'

function statusToProgress(status: Task['status']): number {
  return { todo: 0, in_progress: 50, done: 100 }[status]
}

function toDateStr(date: string | null | undefined, fallback: string): string {
  if (date) return date.split('T')[0]
  return fallback.split('T')[0]
}

function taskToGanttTask(task: Task): GanttTask {
  const today = format(new Date(), 'yyyy-MM-dd')
  const start = toDateStr(task.start_date, task.created_at ?? today)
  const end = toDateStr(task.due_date, start)
  return {
    id: task.id,
    name: task.title,
    start,
    end: end < start ? start : end,
    progress: statusToProgress(task.status),
    dependencies: '',
    custom_class: `priority-${task.priority}`,
  }
}

function milestoneToGanttTask(milestone: Milestone): GanttTask {
  const today = format(new Date(), 'yyyy-MM-dd')
  const date = toDateStr(milestone.target_date, milestone.created_at ?? today)
  return {
    id: `milestone-${milestone.id}`,
    name: `◆ ${milestone.name}`,
    start: date,
    end: date,
    progress: milestone.status === 'completed' ? 100 : 0,
    custom_class: 'milestone-bar',
  }
}

const VIEW_MODES: ViewMode[] = ['Day', 'Week', 'Month']

interface GanttWrapperProps {
  projectId: string
  tasks: Task[]
  onEditTask: (task: Task) => void
}

export function GanttWrapper({ projectId, tasks, onEditTask }: GanttWrapperProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('Week')
  const { data: milestones = [] } = useMilestones(projectId)
  const updateTask = useUpdateTask()

  const ganttTasks: GanttTask[] = [
    ...tasks.map(taskToGanttTask),
    ...milestones.map(milestoneToGanttTask),
  ]

  function handleDateChange(ganttTask: GanttTask, start: Date, end: Date) {
    if (ganttTask.id.startsWith('milestone-')) return
    updateTask.mutate({
      id: ganttTask.id,
      data: {
        start_date: format(start, 'yyyy-MM-dd'),
        due_date: format(end, 'yyyy-MM-dd'),
      },
    })
  }

  function handleTaskClick(ganttTask: GanttTask) {
    if (ganttTask.id.startsWith('milestone-')) return
    const task = tasks.find((t) => t.id === ganttTask.id)
    if (task) onEditTask(task)
  }

  return (
    <div className="space-y-3">
      {/* View mode toolbar */}
      <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 p-0.5 w-fit">
        {VIEW_MODES.map((mode) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            className={cn(
              'rounded-md px-3 py-1 text-xs font-medium transition-colors',
              viewMode === mode
                ? 'bg-white shadow-sm text-slate-900'
                : 'text-slate-500 hover:text-slate-700',
            )}
          >
            {mode}
          </button>
        ))}
      </div>

      <GanttChart
        tasks={ganttTasks}
        viewMode={viewMode}
        onTaskClick={handleTaskClick}
        onDateChange={handleDateChange}
      />
    </div>
  )
}
