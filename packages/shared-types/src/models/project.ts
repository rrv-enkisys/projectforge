export interface Project {
  id: string
  name: string
  description?: string
  organizationId: string
  clientId?: string
  ownerId: string
  status: ProjectStatus
  startDate?: Date
  endDate?: Date
  budget?: number
  currency?: string
  createdAt: Date
  updatedAt: Date
}

export enum ProjectStatus {
  PLANNING = 'PLANNING',
  ACTIVE = 'ACTIVE',
  ON_HOLD = 'ON_HOLD',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
}

export interface ProjectMember {
  projectId: string
  userId: string
  role: ProjectRole
  joinedAt: Date
}

export enum ProjectRole {
  OWNER = 'OWNER',
  MANAGER = 'MANAGER',
  CONTRIBUTOR = 'CONTRIBUTOR',
  VIEWER = 'VIEWER',
}
