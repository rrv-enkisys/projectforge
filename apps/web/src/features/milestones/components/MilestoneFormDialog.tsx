import { useState } from 'react'
import { toast } from 'sonner'
import { MilestoneForm } from './MilestoneForm'
import { useCreateMilestone, useUpdateMilestone, type Milestone } from '../hooks/useMilestones'
import type { MilestoneFormData } from '../schemas'
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

interface MilestoneFormDialogProps {
  milestone?: Milestone
  trigger?: React.ReactNode
  onSuccess?: () => void
  open?: boolean
  onOpenChange?: (open: boolean) => void
  defaultProjectId?: string
}

export function MilestoneFormDialog({
  milestone,
  trigger,
  onSuccess,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
  defaultProjectId,
}: MilestoneFormDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const createMutation = useCreateMilestone()
  const updateMutation = useUpdateMilestone()

  // Use controlled state if provided, otherwise use internal state
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen
  const setOpen = controlledOnOpenChange !== undefined ? controlledOnOpenChange : setInternalOpen

  const handleSubmit = async (data: MilestoneFormData) => {
    try {
      if (milestone) {
        await updateMutation.mutateAsync({
          id: milestone.id,
          data,
        })
        toast.success('Milestone updated successfully')
      } else {
        await createMutation.mutateAsync(data)
        toast.success('Milestone created successfully')
      }

      setOpen(false)
      onSuccess?.()
    } catch (error: any) {
      // Extract error message from Pydantic validation errors
      let message = 'Failed to save milestone'
      if (error?.response?.data?.detail) {
        const detail = error.response.data.detail
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          message = detail.map((err: any) => err.msg).join(', ')
        } else if (typeof detail === 'string') {
          message = detail
        }
      } else if (error?.message) {
        message = error.message
      }
      toast.error(message)
      console.error('Failed to save milestone:', error)
    }
  }

  const isSubmitting = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Milestone
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{milestone ? 'Edit Milestone' : 'Create New Milestone'}</DialogTitle>
          <DialogDescription>
            {milestone
              ? 'Make changes to your milestone below.'
              : 'Fill in the details to create a new milestone.'}
          </DialogDescription>
        </DialogHeader>
        <MilestoneForm
          milestone={milestone}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          defaultProjectId={defaultProjectId}
        />
      </DialogContent>
    </Dialog>
  )
}
