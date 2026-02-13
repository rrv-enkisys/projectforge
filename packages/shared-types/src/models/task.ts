export interface Task {
  id: string
  title: string
  description?: string
  projectId: string
  milestoneId?: string
  assigneeId?: string
  creatorId: string
  status: TaskStatus
  priority: TaskPriority
  estimatedHours?: number
  actualHours?: number
  startDate?: Date
  dueDate?: Date
  completedAt?: Date
  tags: string[]
  dependencies: string[]
  createdAt: Date
  updatedAt: Date
}

export enum TaskStatus {
  TODO = 'TODO',
  IN_PROGRESS = 'IN_PROGRESS',
  IN_REVIEW = 'IN_REVIEW',
  BLOCKED = 'BLOCKED',
  DONE = 'DONE',
}

export enum TaskPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  URGENT = 'URGENT',
}

export interface TaskComment {
  id: string
  taskId: string
  userId: string
  content: string
  createdAt: Date
  updatedAt: Date
}
