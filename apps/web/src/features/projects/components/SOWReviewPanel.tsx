import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useCreateProject } from '../hooks/useProjects'
import { useCreateMilestone } from '@/features/milestones/hooks/useMilestones'
import { useCreateTask } from '@/features/tasks/hooks/useTasks'
import type { SOWParseResponse } from '@/features/ai/hooks/useSOWParser'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Check,
  ChevronDown,
  ChevronRight,
  FolderKanban,
  ListTodo,
  Loader2,
  Milestone,
  AlertTriangle,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface SOWReviewPanelProps {
  result: SOWParseResponse
  onProjectCreated?: (projectId: string) => void
  onReset: () => void
}

function addDays(base: Date, days: number): string {
  const d = new Date(base)
  d.setDate(d.getDate() + days)
  return d.toISOString().split('T')[0]
}

function mapPriority(p: string): 'critical' | 'high' | 'medium' | 'low' {
  return p === 'urgent' ? 'critical' : (p as 'critical' | 'high' | 'medium' | 'low')
}

export function SOWReviewPanel({ result, onProjectCreated, onReset }: SOWReviewPanelProps) {
  const navigate = useNavigate()
  const [projectName, setProjectName] = useState(result.project.name)
  const [projectDescription, setProjectDescription] = useState(result.project.description)
  const [expandedMilestones, setExpandedMilestones] = useState<number[]>([0])
  const [isCreating, setIsCreating] = useState(false)

  const createProject = useCreateProject()
  const createMilestone = useCreateMilestone()
  const createTask = useCreateTask()

  const today = new Date()
  const durationDays = result.project.estimated_duration_days ?? 30
  const startDateStr = today.toISOString().split('T')[0]
  const endDateStr = addDays(today, durationDays)

  const toggleMilestone = (i: number) =>
    setExpandedMilestones(prev =>
      prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i],
    )

  const handleCreateAll = async () => {
    setIsCreating(true)
    try {
      // 1. Create project
      const newProject = await createProject.mutateAsync({
        name: projectName.trim(),
        description: projectDescription,
        start_date: startDateStr,
        end_date: endDateStr,
        budget: result.project.estimated_budget ?? undefined,
        status: 'planning',
      })

      // 2. Create milestones and collect their IDs
      const milestoneIds: string[] = []
      for (const ms of result.milestones) {
        const targetDate =
          ms.target_date_offset_days != null
            ? addDays(today, ms.target_date_offset_days)
            : endDateStr
        const created = await createMilestone.mutateAsync({
          project_id: newProject.id,
          name: ms.title,
          description: ms.description,
          target_date: targetDate,
          status: 'planning',
        })
        milestoneIds.push(created.id)
      }

      // 3. Create tasks
      for (const task of result.tasks) {
        const milestoneId =
          task.milestone_index != null
            ? (milestoneIds[task.milestone_index] ?? null)
            : null
        const offsetForDueDate =
          task.milestone_index != null
            ? (result.milestones[task.milestone_index]?.target_date_offset_days ?? durationDays)
            : durationDays

        await createTask.mutateAsync({
          project_id: newProject.id,
          milestone_id: milestoneId,
          title: task.title,
          description: task.description,
          estimated_hours: task.estimated_hours,
          priority: mapPriority(task.priority),
          status: 'todo',
          due_date: addDays(today, offsetForDueDate),
        })
      }

      toast.success(
        `"${projectName}" created — ${result.milestones.length} milestones, ${result.tasks.length} tasks`,
      )
      onProjectCreated?.(newProject.id)
      navigate(`/projects/${newProject.id}`)
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      const msg =
        Array.isArray(detail)
          ? detail.map((e: any) => e.msg).join(', ')
          : typeof detail === 'string'
          ? detail
          : error?.message || 'Failed to create project'
      toast.error(msg)
    } finally {
      setIsCreating(false)
    }
  }

  const confidencePct = Math.round(result.confidence * 100)
  const confidenceClass =
    result.confidence >= 0.8
      ? 'bg-green-100 text-green-700 border-green-200'
      : result.confidence >= 0.5
      ? 'bg-yellow-100 text-yellow-700 border-yellow-200'
      : 'bg-red-100 text-red-700 border-red-200'

  return (
    <div className="space-y-5 pt-2">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-800">Review Generated Structure</h3>
        <span className={cn('text-xs font-medium px-2.5 py-1 rounded-full border', confidenceClass)}>
          {confidencePct}% confidence
        </span>
      </div>

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-center gap-2 text-yellow-700 font-medium text-sm mb-1">
            <AlertTriangle className="h-4 w-4" />
            Warnings
          </div>
          <ul className="text-xs text-yellow-600 space-y-0.5">
            {result.warnings.map((w, i) => (
              <li key={i}>• {w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Project details — editable name & description */}
      <Card className="p-4 space-y-2">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-1">
          <FolderKanban className="h-4 w-4 text-blue-500" />
          Project
        </div>
        <Input
          value={projectName}
          onChange={e => setProjectName(e.target.value)}
          className="font-medium"
          placeholder="Project name"
        />
        <Textarea
          value={projectDescription}
          onChange={e => setProjectDescription(e.target.value)}
          placeholder="Description"
          rows={2}
          className="text-sm resize-none"
        />
        <div className="flex flex-wrap gap-4 text-xs text-slate-400 pt-1">
          <span>Start: {startDateStr}</span>
          <span>End: {endDateStr}</span>
          {result.project.estimated_budget != null && (
            <span>
              Budget: {result.project.estimated_budget.toLocaleString()} {result.project.currency}
            </span>
          )}
        </div>
      </Card>

      {/* Milestones + Tasks */}
      <div>
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-2">
          <Milestone className="h-4 w-4 text-purple-500" />
          {result.milestones.length} milestone{result.milestones.length !== 1 ? 's' : ''} ·{' '}
          {result.tasks.length} task{result.tasks.length !== 1 ? 's' : ''}
        </div>

        <div className="space-y-2">
          {result.milestones.map((ms, msIdx) => {
            const msTasks = result.tasks.filter(t => t.milestone_index === msIdx)
            const isExpanded = expandedMilestones.includes(msIdx)

            return (
              <Card key={msIdx} className="overflow-hidden">
                <button
                  type="button"
                  onClick={() => toggleMilestone(msIdx)}
                  className="w-full px-3 py-2.5 flex items-center justify-between hover:bg-slate-50 text-left"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {isExpanded ? (
                      <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                    )}
                    <span className="text-sm font-medium truncate">{ms.title}</span>
                    {ms.target_date_offset_days != null && (
                      <span className="text-xs text-slate-400 shrink-0">
                        day {ms.target_date_offset_days}
                      </span>
                    )}
                  </div>
                  <Badge variant="outline" className="text-xs shrink-0 ml-2">
                    {msTasks.length} task{msTasks.length !== 1 ? 's' : ''}
                  </Badge>
                </button>

                {isExpanded && msTasks.length > 0 && (
                  <div className="border-t bg-slate-50 px-3 py-2 space-y-1.5">
                    {msTasks.map((task, tIdx) => (
                      <div key={tIdx} className="flex items-center justify-between text-xs py-0.5">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <ListTodo className="h-3 w-3 text-slate-400 shrink-0" />
                          <span className="truncate text-slate-700">{task.title}</span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0 ml-2">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs py-0',
                              task.priority === 'urgent' && 'border-red-300 text-red-600',
                              task.priority === 'high' && 'border-orange-300 text-orange-600',
                            )}
                          >
                            {task.priority}
                          </Badge>
                          {task.estimated_hours != null && (
                            <span className="text-slate-400">{task.estimated_hours}h</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )
          })}

          {/* Tasks with no milestone */}
          {result.milestones.length === 0 && result.tasks.length > 0 && (
            <Card className="p-3">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-600 mb-2">
                <ListTodo className="h-4 w-4 text-slate-400" />
                Tasks
              </div>
              <div className="space-y-1">
                {result.tasks.map((task, i) => (
                  <div key={i} className="flex items-center justify-between text-xs py-0.5">
                    <span className="text-slate-700 truncate">{task.title}</span>
                    <Badge variant="outline" className="text-xs py-0 ml-2">
                      {task.priority}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-2 border-t">
        <Button
          onClick={handleCreateAll}
          disabled={isCreating || !projectName.trim()}
          className="flex-1"
        >
          {isCreating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating…
            </>
          ) : (
            <>
              <Check className="mr-2 h-4 w-4" />
              Create Project
            </>
          )}
        </Button>
        <Button variant="outline" onClick={onReset} disabled={isCreating}>
          <X className="mr-2 h-4 w-4" />
          Cancel
        </Button>
      </div>
    </div>
  )
}
