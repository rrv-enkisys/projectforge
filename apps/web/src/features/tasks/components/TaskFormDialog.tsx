import { useState } from 'react'
import { toast } from 'sonner'
import { TaskForm } from './TaskForm'
import { useCreateTask, useUpdateTask, type Task } from '../hooks/useTasks'
import type { TaskFormData } from '../schemas'
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

interface TaskFormDialogProps {
  task?: Task
  trigger?: React.ReactNode
  onSuccess?: () => void
  open?: boolean
  onOpenChange?: (open: boolean) => void
  defaultProjectId?: string
}

export function TaskFormDialog({
  task,
  trigger,
  onSuccess,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
  defaultProjectId,
}: TaskFormDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const createMutation = useCreateTask()
  const updateMutation = useUpdateTask()

  // Use controlled state if provided, otherwise use internal state
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen
  const setOpen = controlledOnOpenChange !== undefined ? controlledOnOpenChange : setInternalOpen

  const handleSubmit = async (data: TaskFormData) => {
    try {
      if (task) {
        await updateMutation.mutateAsync({
          id: task.id,
          data,
        })
        toast.success('Task updated successfully')
      } else {
        await createMutation.mutateAsync(data)
        toast.success('Task created successfully')
      }

      setOpen(false)
      onSuccess?.()
    } catch (error: any) {
      // Extract error message from Pydantic validation errors
      let message = 'Failed to save task'
      if (error?.response?.data?.detail) {
        const detail = error.response.data.detail
        if (Array.isArray(detail)) {
          message = detail.map((err: any) => err.msg).join(', ')
        } else if (typeof detail === 'string') {
          message = detail
        }
      } else if (error?.message) {
        message = error.message
      }
      toast.error(message)
      console.error('Failed to save task:', error)
    }
  }

  const isSubmitting = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Task
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{task ? 'Edit Task' : 'Create New Task'}</DialogTitle>
          <DialogDescription>
            {task ? 'Make changes to your task below.' : 'Fill in the details to create a new task.'}
          </DialogDescription>
        </DialogHeader>
        <TaskForm
          task={task}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          defaultProjectId={defaultProjectId}
        />
      </DialogContent>
    </Dialog>
  )
}
