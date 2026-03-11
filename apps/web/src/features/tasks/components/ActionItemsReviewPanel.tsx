import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from 'sonner'
import { CheckCircle2, ChevronDown, ChevronRight, Flag, Loader2, User } from 'lucide-react'
import { type MeetingNotesParseResponse, type ActionItem } from '@/features/ai/hooks/useMeetingNotes'
import { useCreateTask } from '@/features/tasks/hooks/useTasks'
import { useProjects } from '@/features/projects/hooks/useProjects'

interface ActionItemsReviewPanelProps {
  result: MeetingNotesParseResponse
  onDone: () => void
}

function mapPriority(p: string): 'critical' | 'high' | 'medium' | 'low' {
  if (p === 'urgent') return 'critical'
  if (p === 'high') return 'high'
  if (p === 'low') return 'low'
  return 'medium'
}

function addDays(base: Date, days: number): string {
  const d = new Date(base)
  d.setDate(d.getDate() + days)
  return d.toISOString().split('T')[0]
}

function parseDueDateHint(hint: string | null): string {
  const today = new Date()
  if (!hint) return addDays(today, 7)
  const lower = hint.toLowerCase()
  if (lower.includes('today') || lower.includes('eod') || lower.includes('end of day')) return addDays(today, 0)
  if (lower.includes('tomorrow')) return addDays(today, 1)
  if (lower.includes('thursday')) return addDays(today, ((4 - today.getDay() + 7) % 7) || 7)
  if (lower.includes('friday')) return addDays(today, ((5 - today.getDay() + 7) % 7) || 7)
  if (lower.includes('monday')) return addDays(today, ((1 - today.getDay() + 7) % 7) || 7)
  if (lower.includes('next week') || lower.includes('end of week')) return addDays(today, 7)
  if (lower.includes('next monday')) return addDays(today, ((1 - today.getDay() + 7) % 7) + 7)
  return addDays(today, 7)
}

const priorityColors: Record<string, string> = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700',
}

export function ActionItemsReviewPanel({ result, onDone }: ActionItemsReviewPanelProps) {
  const { analysis } = result
  const [selectedIds, setSelectedIds] = useState<Set<number>>(
    new Set(analysis.action_items.map((_, i) => i)),
  )
  const [projectId, setProjectId] = useState<string>('')
  const [showDecisions, setShowDecisions] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [createdCount, setCreatedCount] = useState(0)

  const { data: projectsData } = useProjects(0, 100)
  const createTask = useCreateTask()

  const toggleItem = (idx: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  const handleCreate = async () => {
    if (!projectId) {
      toast.error('Please select a project first.')
      return
    }
    const items = analysis.action_items.filter((_, i) => selectedIds.has(i))
    if (items.length === 0) {
      toast.error('Select at least one action item.')
      return
    }

    setIsCreating(true)
    setCreatedCount(0)
    let count = 0

    for (const item of items) {
      try {
        await createTask.mutateAsync({
          title: item.description,
          description: item.context ?? undefined,
          project_id: projectId,
          priority: mapPriority(item.priority),
          due_date: parseDueDateHint(item.due_date_hint),
        })
        count++
        setCreatedCount(count)
      } catch {
        toast.error(`Failed to create: "${item.description}"`)
      }
    }

    setIsCreating(false)
    toast.success(`${count} task${count !== 1 ? 's' : ''} created successfully.`)
    onDone()
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card className="p-4 bg-slate-50 border-slate-200">
        <p className="text-sm text-slate-700 leading-relaxed">{analysis.summary}</p>
        <div className="flex flex-wrap gap-2 mt-3">
          {analysis.participants_detected.map((p) => (
            <Badge key={p} variant="secondary" className="text-xs">
              <User className="h-3 w-3 mr-1" />
              {p}
            </Badge>
          ))}
          {analysis.meeting_date_hint && (
            <Badge variant="outline" className="text-xs">
              {analysis.meeting_date_hint}
            </Badge>
          )}
          <Badge
            variant="outline"
            className={`text-xs ${analysis.confidence >= 0.7 ? 'text-green-700 border-green-300' : 'text-orange-700 border-orange-300'}`}
          >
            {Math.round(analysis.confidence * 100)}% confidence
          </Badge>
        </div>
      </Card>

      {/* Project selector */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Create tasks in project <span className="text-red-500">*</span>
        </label>
        <Select value={projectId} onValueChange={setProjectId}>
          <SelectTrigger>
            <SelectValue placeholder="Select a project…" />
          </SelectTrigger>
          <SelectContent>
            {projectsData?.data.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Action items */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-900">
            Action Items ({selectedIds.size} of {analysis.action_items.length} selected)
          </h3>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs"
              onClick={() => setSelectedIds(new Set(analysis.action_items.map((_, i) => i)))}
            >
              Select all
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs"
              onClick={() => setSelectedIds(new Set())}
            >
              Clear
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          {analysis.action_items.map((item: ActionItem, i: number) => (
            <div
              key={i}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedIds.has(i) ? 'bg-blue-50 border-blue-200' : 'bg-white border-slate-200'
              }`}
              onClick={() => toggleItem(i)}
            >
              <Checkbox
                checked={selectedIds.has(i)}
                onCheckedChange={() => toggleItem(i)}
                className="mt-0.5"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-900">{item.description}</p>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  <Badge className={`text-xs px-1.5 py-0 ${priorityColors[item.priority]}`}>
                    <Flag className="h-2.5 w-2.5 mr-1" />
                    {item.priority}
                  </Badge>
                  {item.assignee_hint && (
                    <Badge variant="secondary" className="text-xs px-1.5 py-0">
                      <User className="h-2.5 w-2.5 mr-1" />
                      {item.assignee_hint}
                    </Badge>
                  )}
                  {item.due_date_hint && (
                    <Badge variant="outline" className="text-xs px-1.5 py-0">
                      {item.due_date_hint}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Decisions (collapsible) */}
      {analysis.decisions.length > 0 && (
        <div>
          <button
            className="flex items-center gap-1 text-sm font-medium text-slate-700 hover:text-slate-900"
            onClick={() => setShowDecisions((v) => !v)}
          >
            {showDecisions ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            Decisions ({analysis.decisions.length})
          </button>
          {showDecisions && (
            <div className="mt-2 space-y-1.5">
              {analysis.decisions.map((d, i) => (
                <div key={i} className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200">
                  <CheckCircle2 className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm text-slate-800">{d.description}</p>
                    {d.made_by_hint && (
                      <p className="text-xs text-slate-500 mt-0.5">by {d.made_by_hint}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Warnings */}
      {analysis.warnings.length > 0 && (
        <div className="p-3 rounded-lg bg-orange-50 border border-orange-200">
          {analysis.warnings.map((w, i) => (
            <p key={i} className="text-xs text-orange-800">{w}</p>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t">
        <Button variant="ghost" onClick={onDone} disabled={isCreating}>
          Cancel
        </Button>
        <Button
          onClick={handleCreate}
          disabled={isCreating || selectedIds.size === 0 || !projectId}
        >
          {isCreating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating {createdCount}/{selectedIds.size}…
            </>
          ) : (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Create {selectedIds.size} Task{selectedIds.size !== 1 ? 's' : ''}
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
