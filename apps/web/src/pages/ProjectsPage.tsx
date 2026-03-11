import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Plus, Wand2 } from 'lucide-react'
import { useProjects } from '@/features/projects/hooks/useProjects'
import { ProjectCard } from '@/features/projects/components/ProjectCard'
import { ProjectFormDialog } from '@/features/projects/components/ProjectFormDialog'
import { SOWUploader } from '@/features/projects/components/SOWUploader'
import type { Project } from '@/features/projects/types'

export default function ProjectsPage() {
  const { data, isLoading, error } = useProjects()
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [isFormDialogOpen, setIsFormDialogOpen] = useState(false)
  const [isSOWDialogOpen, setIsSOWDialogOpen] = useState(false)

  const handleEdit = (project: Project) => {
    setEditingProject(project)
    setIsFormDialogOpen(true)
  }

  const handleFormDialogClose = () => {
    setIsFormDialogOpen(false)
    setEditingProject(null)
  }

  const handleProjectCreatedFromSOW = (_projectId: string) => {
    setIsSOWDialogOpen(false)
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Projects</h1>
            <p className="mt-2 text-sm text-slate-600">
              Manage and track all your projects in one place
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Create from SOW button */}
            <Button variant="outline" onClick={() => setIsSOWDialogOpen(true)}>
              <Wand2 className="mr-2 h-4 w-4 text-purple-500" />
              Create from SOW
            </Button>

            {/* New Project button */}
            <ProjectFormDialog
              project={editingProject || undefined}
              open={isFormDialogOpen}
              onOpenChange={open => {
                setIsFormDialogOpen(open)
                if (!open) setEditingProject(null)
              }}
              onSuccess={handleFormDialogClose}
              trigger={
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Project
                </Button>
              }
            />
          </div>
        </div>

        {/* Projects grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">Failed to load projects. Please try again.</p>
          </div>
        ) : data?.data && data.data.length > 0 ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {data.data.map(project => (
              <ProjectCard key={project.id} project={project} onEdit={handleEdit} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-slate-600">
              No projects yet.{' '}
              <button
                className="text-purple-600 hover:underline"
                onClick={() => setIsSOWDialogOpen(true)}
              >
                Import from a SOW
              </button>{' '}
              or create one manually.
            </p>
          </div>
        )}
      </div>

      {/* SOW Uploader Dialog */}
      <Dialog open={isSOWDialogOpen} onOpenChange={setIsSOWDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" aria-describedby={undefined}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-purple-500" />
              Create Project from SOW
            </DialogTitle>
            <DialogDescription>
              Upload a Statement of Work (PDF, DOCX, TXT, or Markdown) and AI will
              generate the project structure for you to review and import.
            </DialogDescription>
          </DialogHeader>
          <SOWUploader onProjectCreated={handleProjectCreatedFromSOW} />
        </DialogContent>
      </Dialog>
    </AppLayout>
  )
}
