export interface Project {
  id: string
  name: string
  description: string
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled'
  start_date: string
  end_date: string | null
  budget: number | null
  client_id: string | null
  organization_id: string
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  data: Project[]
  total: number
  has_more: boolean
}
