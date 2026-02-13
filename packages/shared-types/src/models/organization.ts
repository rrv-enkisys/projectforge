export interface Organization {
  id: string
  name: string
  slug: string
  logo?: string
  plan: SubscriptionPlan
  settings: OrganizationSettings
  createdAt: Date
  updatedAt: Date
}

export enum SubscriptionPlan {
  FREE = 'FREE',
  PRO = 'PRO',
  ENTERPRISE = 'ENTERPRISE',
}

export interface OrganizationSettings {
  allowGuestAccess: boolean
  requireMfa: boolean
  customDomain?: string
  features: {
    aiCopilot: boolean
    advancedReporting: boolean
    customFields: boolean
  }
}
