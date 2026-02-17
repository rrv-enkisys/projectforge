import { z } from 'zod'

export const projectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(255, 'Name is too long'),
  description: z.string().optional(),
  client_id: z.string().uuid('Invalid client').nullable().optional(),
  start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format (YYYY-MM-DD)'),
  end_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format (YYYY-MM-DD)')
    .nullable()
    .optional(),
  status: z.enum(['planning', 'active', 'on_hold', 'completed', 'cancelled']).default('planning'),
  budget: z.number().positive('Budget must be positive').nullable().optional(),
})

export type ProjectFormData = z.infer<typeof projectSchema>
