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
    on_view_change?: (mode: { name: ViewMode }) => void
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
