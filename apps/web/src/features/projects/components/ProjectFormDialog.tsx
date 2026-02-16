import { useState } from 'react'
import { toast } from 'sonner'
import { ProjectForm } from './ProjectForm'
import { useCreateProject, useUpdateProject } from '../hooks/useProjects'
import type { Project } from '../types'
import type { ProjectFormData } from '../schemas'
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

interface ProjectFormDialogProps {
  project?: Project
  trigger?: React.ReactNode
  onSuccess?: () => void
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function ProjectFormDialog({
  project,
  trigger,
  onSuccess,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: ProjectFormDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const createMutation = useCreateProject()
  const updateMutation = useUpdateProject()

  // Use controlled state if provided, otherwise use internal state
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen
  const setOpen = controlledOnOpenChange !== undefined ? controlledOnOpenChange : setInternalOpen

  const handleSubmit = async (data: ProjectFormData) => {
    try {
      if (project) {
        await updateMutation.mutateAsync({
          id: project.id,
          data,
        })
        toast.success('Project updated successfully')
      } else {
        await createMutation.mutateAsync(data)
        toast.success('Project created successfully')
      }

      setOpen(false)
      onSuccess?.()
    } catch (error: any) {
      // Extract error message from Pydantic validation errors
      let message = 'Failed to save project'
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
      console.error('Failed to save project:', error)
    }
  }

  const isSubmitting = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{project ? 'Edit Project' : 'Create New Project'}</DialogTitle>
          <DialogDescription>
            {project
              ? 'Make changes to your project below.'
              : 'Fill in the details to create a new project.'}
          </DialogDescription>
        </DialogHeader>
        <ProjectForm project={project} onSubmit={handleSubmit} isSubmitting={isSubmitting} />
      </DialogContent>
    </Dialog>
  )
}
