import { useState } from 'react'
import { toast } from 'sonner'
import { AppLayout } from '@/components/layout/AppLayout'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Plus, Calendar, MoreVertical, Pencil, Trash2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MilestoneFormDialog } from '@/features/milestones/components/MilestoneFormDialog'
import { useMilestones, useDeleteMilestone, type Milestone } from '@/features/milestones/hooks/useMilestones'

const statusColors = {
  planning: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
  active: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
  on_hold: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
  completed: 'bg-green-100 text-green-800 hover:bg-green-200',
  archived: 'bg-slate-100 text-slate-800 hover:bg-slate-200',
}

const statusLabels = {
  planning: 'Planning',
  active: 'Active',
  on_hold: 'On Hold',
  completed: 'Completed',
  archived: 'Archived',
}

export default function MilestonesPage() {
  const { data: milestones, isLoading } = useMilestones()
  const deleteMutation = useDeleteMilestone()
  const [editingMilestone, setEditingMilestone] = useState<Milestone | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete milestone "${name}"?`)) {
      return
    }

    try {
      await deleteMutation.mutateAsync(id)
      toast.success('Milestone deleted successfully')
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || 'Failed to delete milestone'
      toast.error(message)
    }
  }

  const handleEdit = (milestone: Milestone) => {
    setEditingMilestone(milestone)
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
    setEditingMilestone(null)
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Milestones</h1>
            <p className="text-muted-foreground">Track important project milestones and deadlines</p>
          </div>
          <MilestoneFormDialog
            milestone={editingMilestone || undefined}
            open={isDialogOpen}
            onOpenChange={(open) => {
              setIsDialogOpen(open)
              if (!open) setEditingMilestone(null)
            }}
            onSuccess={handleDialogClose}
            trigger={
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Milestone
              </Button>
            }
          />
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-3 bg-gray-100 rounded w-1/2"></div>
              </Card>
            ))}
          </div>
        ) : milestones && milestones.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {milestones.map((milestone) => (
              <Card key={milestone.id} className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-2">{milestone.name}</h3>
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[milestone.status]}`}>
                      {statusLabels[milestone.status]}
                    </span>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleEdit(milestone)}>
                        <Pencil className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleDelete(milestone.id, milestone.name)}
                        className="text-red-600"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {milestone.description && (
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                    {milestone.description}
                  </p>
                )}

                {milestone.target_date && (
                  <div className="flex items-center text-sm text-muted-foreground">
                    <Calendar className="mr-2 h-4 w-4" />
                    Target: {new Date(milestone.target_date).toLocaleDateString()}
                  </div>
                )}

                {milestone.completed_date && (
                  <div className="flex items-center text-sm text-green-600 mt-2">
                    <Calendar className="mr-2 h-4 w-4" />
                    Completed: {new Date(milestone.completed_date).toLocaleDateString()}
                  </div>
                )}
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center">
            <p className="text-muted-foreground mb-4">No milestones yet</p>
            <MilestoneFormDialog
              trigger={
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Milestone
                </Button>
              }
            />
          </Card>
        )}
      </div>
    </AppLayout>
  )
}
