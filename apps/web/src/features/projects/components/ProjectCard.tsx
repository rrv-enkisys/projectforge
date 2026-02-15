import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Project } from '../types'
import { Calendar, DollarSign } from 'lucide-react'
import { format } from 'date-fns'
import { cn } from '@/lib/utils'

interface ProjectCardProps {
  project: Project
}

const statusColors = {
  planning: 'bg-yellow-100 text-yellow-800',
  active: 'bg-green-100 text-green-800',
  on_hold: 'bg-orange-100 text-orange-800',
  completed: 'bg-blue-100 text-blue-800',
  cancelled: 'bg-red-100 text-red-800',
}

const statusLabels = {
  planning: 'Planning',
  active: 'Active',
  on_hold: 'On Hold',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link to={`/projects/${project.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg">{project.name}</CardTitle>
              <CardDescription className="mt-1 line-clamp-2">{project.description}</CardDescription>
            </div>
            <span
              className={cn(
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ml-2',
                statusColors[project.status]
              )}
            >
              {statusLabels[project.status]}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-1" />
              <span>{format(new Date(project.start_date), 'MMM d, yyyy')}</span>
            </div>
            {project.budget && (
              <div className="flex items-center">
                <DollarSign className="h-4 w-4 mr-1" />
                <span>${project.budget.toLocaleString()}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
