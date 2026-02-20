import { z } from 'zod'

export const taskSchema = z.object({
  title: z.string().min(1, 'Task title is required').max(255, 'Title is too long'),
  description: z.string().optional(),
  project_id: z.string().uuid('Invalid project'),
  milestone_id: z.string().uuid('Invalid milestone').nullable().optional(),
  parent_task_id: z.string().uuid('Invalid parent task').nullable().optional(),
  status: z.enum(['todo', 'in_progress', 'done']),
  priority: z.enum(['critical', 'high', 'medium', 'low']),
  start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format (YYYY-MM-DD)').optional(),
  due_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format (YYYY-MM-DD)'),
  estimated_hours: z.number().positive('Must be positive').nullable().optional(),
  actual_hours: z.number().positive('Must be positive').nullable().optional(),
})

export type TaskFormData = z.infer<typeof taskSchema>
