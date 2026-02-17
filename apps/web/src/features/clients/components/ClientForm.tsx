import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { clientSchema, type ClientFormData } from '../schemas'
import type { Client } from '../hooks/useClients'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'

interface ClientFormProps {
  client?: Client
  onSubmit: (data: ClientFormData) => void
  isSubmitting?: boolean
}

export function ClientForm({ client, onSubmit, isSubmitting }: ClientFormProps) {
  const form = useForm<ClientFormData>({
    resolver: zodResolver(clientSchema),
    defaultValues: {
      name: '',
      contact_name: '',
      contact_email: '',
      contact_phone: '',
      address: '',
    },
  })

  // Load client data when editing
  useEffect(() => {
    if (client) {
      form.reset({
        name: client.name,
        contact_name: client.contact_info?.contact_name || '',
        contact_email: client.contact_info?.email || '',
        contact_phone: client.contact_info?.phone || '',
        address: client.contact_info?.address || '',
      })
    }
  }, [client, form])

  const handleFormSubmit = (data: ClientFormData) => {
    // Transform data to match API structure
    const apiData = {
      name: data.name,
      contact_info: {
        contact_name: data.contact_name,
        email: data.contact_email,
        phone: data.contact_phone,
        address: data.address,
      },
    }
    onSubmit(apiData as any)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Client Name *</FormLabel>
              <FormControl>
                <Input placeholder="Enter client name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="contact_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Contact Name</FormLabel>
              <FormControl>
                <Input placeholder="Enter contact person name" {...field} value={field.value || ''} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="contact_email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Contact Email</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder="contact@example.com"
                    {...field}
                    value={field.value || ''}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="contact_phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Contact Phone</FormLabel>
                <FormControl>
                  <Input placeholder="+1 (555) 000-0000" {...field} value={field.value || ''} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="address"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Address</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter client address"
                  {...field}
                  value={field.value || ''}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-2 pt-4">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : client ? 'Update Client' : 'Create Client'}
          </Button>
        </div>
      </form>
    </Form>
  )
}
