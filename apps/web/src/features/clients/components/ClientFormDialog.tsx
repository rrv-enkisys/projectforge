import { useState } from 'react'
import { toast } from 'sonner'
import { ClientForm } from './ClientForm'
import { useCreateClient, useUpdateClient, type Client } from '../hooks/useClients'
import type { ClientFormData } from '../schemas'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'

interface ClientFormDialogProps {
  client?: Client
  trigger?: React.ReactNode
  onSuccess?: () => void
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function ClientFormDialog({
  client,
  trigger,
  onSuccess,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: ClientFormDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const createMutation = useCreateClient()
  const updateMutation = useUpdateClient()

  // Use controlled state if provided, otherwise use internal state
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen
  const setOpen = controlledOnOpenChange !== undefined ? controlledOnOpenChange : setInternalOpen

  const handleSubmit = async (data: ClientFormData) => {
    try {
      if (client) {
        await updateMutation.mutateAsync({
          id: client.id,
          data: data as any,
        })
        toast.success('Client updated successfully')
      } else {
        await createMutation.mutateAsync(data as any)
        toast.success('Client created successfully')
      }

      setOpen(false)
      onSuccess?.()
    } catch (error: any) {
      const message = error?.response?.data?.detail ||
                      error?.message ||
                      'Failed to save client'
      toast.error(message)
      console.error('Failed to save client:', error)
    }
  }

  const isSubmitting = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Client
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{client ? 'Edit Client' : 'Create New Client'}</DialogTitle>
          <DialogDescription>
            {client
              ? 'Make changes to your client below.'
              : 'Fill in the details to create a new client.'}
          </DialogDescription>
        </DialogHeader>
        <ClientForm client={client} onSubmit={handleSubmit} isSubmitting={isSubmitting} />
      </DialogContent>
    </Dialog>
  )
}
