import { z } from 'zod'

export const clientSchema = z.object({
  name: z.string().min(1, 'Client name is required').max(255, 'Name is too long'),
  contact_name: z.string().optional(),
  contact_email: z.string().email('Invalid email').optional().or(z.literal('')),
  contact_phone: z.string().optional(),
  address: z.string().optional(),
})

export type ClientFormData = z.infer<typeof clientSchema>
