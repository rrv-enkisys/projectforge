import { TaskStatus, TaskPriority, ProjectStatus } from '../models'

// Project requests
export interface CreateProjectRequest {
  name: string
  description?: string
  clientId?: string
  startDate?: string
  endDate?: string
  budget?: number
  currency?: string
}

export interface UpdateProjectRequest {
  name?: string
  description?: string
  status?: ProjectStatus
  startDate?: string
  endDate?: string
  budget?: number
}

// Task requests
export interface CreateTaskRequest {
  title: string
  description?: string
  projectId: string
  milestoneId?: string
  assigneeId?: string
  status?: TaskStatus
  priority?: TaskPriority
  estimatedHours?: number
  startDate?: string
  dueDate?: string
  tags?: string[]
  dependencies?: string[]
}

export interface UpdateTaskRequest {
  title?: string
  description?: string
  assigneeId?: string
  status?: TaskStatus
  priority?: TaskPriority
  estimatedHours?: number
  actualHours?: number
  startDate?: string
  dueDate?: string
  tags?: string[]
  dependencies?: string[]
}

// Pagination
export interface PaginationParams {
  cursor?: string
  limit?: number
}
