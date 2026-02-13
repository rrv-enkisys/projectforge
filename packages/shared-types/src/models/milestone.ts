export interface Milestone {
  id: string
  name: string
  description?: string
  projectId: string
  dueDate?: Date
  completedAt?: Date
  status: MilestoneStatus
  order: number
  createdAt: Date
  updatedAt: Date
}

export enum MilestoneStatus {
  NOT_STARTED = 'NOT_STARTED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  OVERDUE = 'OVERDUE',
}
