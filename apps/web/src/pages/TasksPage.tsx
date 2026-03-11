import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useTasks, useDeleteTask, type Task } from '@/features/tasks/hooks/useTasks'
import { TaskFormDialog } from '@/features/tasks/components/TaskFormDialog'
import { MeetingNotesUploader } from '@/features/tasks/components/MeetingNotesUploader'
import { Calendar, Flag, MoreVertical, Pencil, Plus, Trash2, FileText } from 'lucide-react'

const statusColors: Record<string, string> = {
  todo: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-yellow-100 text-yellow-700',
  done: 'bg-green-100 text-green-700',
}

const priorityColors: Record<string, string> = {
  low: 'text-slate-500',
  medium: 'text-blue-500',
  high: 'text-orange-500',
  critical: 'text-red-500',
}

interface TaskCardProps {
  task: Task
  onEdit: (task: Task) => void
}

function TaskCard({ task, onEdit }: TaskCardProps) {
  const deleteMutation = useDeleteTask()

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (window.confirm(`Are you sure you want to delete "${task.title}"?`)) {
      try {
        await deleteMutation.mutateAsync(task.id)
      } catch (error) {
        console.error('Failed to delete task:', error)
        alert('Failed to delete task. Please try again.')
      }
    }
  }

  const handleEditClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    onEdit(task)
  }

  return (
    <Card className="p-6 hover:shadow-md transition-shadow group relative">
      <div className="flex items-start justify-between">
        <div className="flex-1 pr-8">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-slate-900">{task.title}</h3>
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium ${
                statusColors[task.status] || 'bg-slate-100'
              }`}
            >
              {task.status.replace('_', ' ')}
            </span>
          </div>
          {task.description && <p className="text-sm text-slate-600 mb-3">{task.description}</p>}
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <div className="flex items-center gap-1">
              <Flag className={`h-4 w-4 ${priorityColors[task.priority]}`} />
              <span className="capitalize">{task.priority}</span>
            </div>
            {task.due_date && (
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>{new Date(task.due_date).toLocaleDateString()}</span>
              </div>
            )}
            {task.estimated_hours && <span>{task.estimated_hours}h estimated</span>}
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleEditClick}>
              <Pencil className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleDelete} className="text-red-600">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </Card>
  )
}

export default function TasksPage() {
  const { data, isLoading, error } = useTasks()
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isMeetingDialogOpen, setIsMeetingDialogOpen] = useState(false)

  const handleEdit = (task: Task) => {
    setEditingTask(task)
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
    setEditingTask(null)
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Tasks</h1>
            <p className="mt-2 text-sm text-slate-600">Track and manage all your tasks across projects</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setIsMeetingDialogOpen(true)}>
              <FileText className="mr-2 h-4 w-4" />
              From Meeting Notes
            </Button>
            <TaskFormDialog
              task={editingTask || undefined}
              open={isDialogOpen}
              onOpenChange={(open) => {
                setIsDialogOpen(open)
                if (!open) setEditingTask(null)
              }}
              onSuccess={handleDialogClose}
              trigger={
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Task
                </Button>
              }
            />
          </div>
        </div>

        {/* Meeting Notes Dialog */}
        <Dialog open={isMeetingDialogOpen} onOpenChange={setIsMeetingDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Extract Tasks from Meeting Notes</DialogTitle>
            </DialogHeader>
            <MeetingNotesUploader onDone={() => setIsMeetingDialogOpen(false)} />
          </DialogContent>
        </Dialog>

        {/* Tasks list */}
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">Failed to load tasks. Please try again.</p>
          </div>
        ) : data?.data && data.data.length > 0 ? (
          <div className="space-y-4">
            {data.data.map((task) => (
              <TaskCard key={task.id} task={task} onEdit={handleEdit} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-slate-600">No tasks found. Create your first task to get started.</p>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
