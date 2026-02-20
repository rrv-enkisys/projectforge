import { useEffect, useRef } from 'react'
import Gantt from 'frappe-gantt'
import type { GanttTask, ViewMode } from 'frappe-gantt'
import '@/styles/gantt.css'

interface GanttChartProps {
  tasks: GanttTask[]
  viewMode: ViewMode
  onTaskClick: (task: GanttTask) => void
  onDateChange: (task: GanttTask, start: Date, end: Date) => void
}

export function GanttChart({ tasks, viewMode, onTaskClick, onDateChange }: GanttChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const ganttRef = useRef<Gantt | null>(null)
  const viewModeRef = useRef<ViewMode>(viewMode)

  // Track latest callbacks without recreating Gantt instance
  const onTaskClickRef = useRef(onTaskClick)
  const onDateChangeRef = useRef(onDateChange)
  useEffect(() => { onTaskClickRef.current = onTaskClick }, [onTaskClick])
  useEffect(() => { onDateChangeRef.current = onDateChange }, [onDateChange])

  // Initialize or refresh Gantt when tasks change
  useEffect(() => {
    if (!containerRef.current || tasks.length === 0) {
      if (containerRef.current) containerRef.current.innerHTML = ''
      ganttRef.current = null
      return
    }

    if (ganttRef.current) {
      ganttRef.current.refresh(tasks)
    } else {
      ganttRef.current = new Gantt(containerRef.current, tasks, {
        view_mode: viewModeRef.current,
        bar_height: 28,
        padding: 10,
        bar_corner_radius: 4,
        on_click: (task) => onTaskClickRef.current(task),
        on_date_change: (task, start, end) => onDateChangeRef.current(task, start, end),
        custom_popup_html: null,
      })
    }

    return () => {
      if (containerRef.current) containerRef.current.innerHTML = ''
      ganttRef.current = null
    }
    // Only re-run when tasks change (reference or length)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tasks])

  // Change view mode without recreating instance
  useEffect(() => {
    viewModeRef.current = viewMode
    if (ganttRef.current) {
      ganttRef.current.change_view_mode(viewMode)
    }
  }, [viewMode])

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 text-sm text-slate-400">
        No tasks to display on the Gantt chart
      </div>
    )
  }

  return <div ref={containerRef} className="gantt-container min-h-[300px]" />
}
