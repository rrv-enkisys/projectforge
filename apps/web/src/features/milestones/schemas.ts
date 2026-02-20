import { z } from 'zod'

export const milestoneSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name must be less than 255 characters'),
  description: z.string().optional(),
  project_id: z.string().uuid('Invalid project ID'),
  target_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format').optional(),
  status: z.enum(['planning', 'active', 'on_hold', 'completed', 'archived']),
})

export type MilestoneFormData = z.infer<typeof milestoneSchema>
