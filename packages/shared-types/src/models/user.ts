export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: UserRole
  organizationId: string
  createdAt: Date
  updatedAt: Date
}

export enum UserRole {
  OWNER = 'OWNER',
  ADMIN = 'ADMIN',
  MEMBER = 'MEMBER',
  GUEST = 'GUEST',
}

export interface UserProfile {
  userId: string
  bio?: string
  timezone?: string
  locale?: string
  preferences: Record<string, unknown>
}
