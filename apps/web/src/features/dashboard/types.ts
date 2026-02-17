export interface RecentProject {
  id: string
  name: string
  status: string
  updated_at: string
}

export interface UpcomingTask {
  id: string
  title: string
  due_date: string | null
  priority: string
  status: string
  project_id: string
}

export interface DashboardStats {
  active_projects: number
  total_clients: number
  documents: number
  completed_tasks_this_week: number
  recent_projects: RecentProject[]
  upcoming_tasks: UpcomingTask[]
}

export interface DashboardStatsResponse {
  data: DashboardStats
}
