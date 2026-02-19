import { useState } from 'react'
import { Sparkles, TrendingUp, AlertTriangle, CheckCircle, Clock, Lightbulb, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAnalyzeProject } from '../hooks/useCopilot'
import type { ProjectAnalysis } from '../hooks/useCopilot'

interface CopilotPanelProps {
  projectId: string
}

const healthColors: Record<string, string> = {
  healthy: 'text-green-600 bg-green-50 border-green-200',
  at_risk: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  critical: 'text-red-600 bg-red-50 border-red-200',
  unknown: 'text-slate-600 bg-slate-50 border-slate-200',
}

const healthIcons: Record<string, React.ReactNode> = {
  healthy: <CheckCircle className="h-5 w-5" />,
  at_risk: <AlertTriangle className="h-5 w-5" />,
  critical: <AlertTriangle className="h-5 w-5" />,
  unknown: <Clock className="h-5 w-5" />,
}

const severityColors: Record<string, string> = {
  low: 'bg-blue-100 text-blue-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-red-100 text-red-700',
}

function MetricCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3 text-center">
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      <p className="text-xs font-medium text-slate-600 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  )
}

export function CopilotPanel({ projectId }: CopilotPanelProps) {
  const [analysis, setAnalysis] = useState<ProjectAnalysis | null>(null)
  const analyzeProject = useAnalyzeProject()

  const handleAnalyze = async () => {
    const result = await analyzeProject.mutateAsync(projectId)
    setAnalysis(result)
  }

  if (analyzeProject.isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-violet-600">
          <Sparkles className="h-8 w-8 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900">AI Project Copilot</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm">
            Get an intelligent analysis of your project health, risks, and actionable recommendations
          </p>
        </div>
        <Button onClick={handleAnalyze} className="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700">
          <Sparkles className="mr-2 h-4 w-4" />
          Analyze Project
        </Button>
      </div>
    )
  }

  const { health, risks, suggestions, timeline, metrics } = analysis

  return (
    <div className="space-y-5">
      {/* Header with re-analyze */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">AI Analysis Results</h3>
        <Button variant="ghost" size="sm" onClick={handleAnalyze}>
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Re-analyze
        </Button>
      </div>

      {/* Health Status */}
      <div className={`flex items-center gap-3 rounded-lg border p-4 ${healthColors[health.status] || healthColors.unknown}`}>
        {healthIcons[health.status]}
        <div>
          <p className="font-semibold capitalize">{health.status.replace('_', ' ')} — Score: {health.score}/100</p>
          <p className="text-sm mt-0.5">{health.message}</p>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <MetricCard
          label="Completion"
          value={`${Math.round(metrics.completion_rate * 100)}%`}
          sub={`${metrics.completed_tasks}/${metrics.total_tasks} tasks`}
        />
        <MetricCard
          label="Overdue Tasks"
          value={metrics.overdue_tasks}
          sub={metrics.overdue_tasks > 0 ? 'Need attention' : 'All on time'}
        />
        <MetricCard
          label="Milestones"
          value={`${metrics.completed_milestones}/${metrics.total_milestones}`}
          sub="completed"
        />
      </div>

      {/* Timeline prediction */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-600" />
            Timeline Prediction
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-600">On Track</span>
            <span className={timeline.on_track ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
              {timeline.on_track ? 'Yes' : 'No'}
            </span>
          </div>
          {timeline.predicted_completion && (
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Predicted Completion</span>
              <span className="font-medium text-slate-900">
                {new Date(timeline.predicted_completion).toLocaleDateString()}
              </span>
            </div>
          )}
          {timeline.delay_days > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Projected Delay</span>
              <span className="font-medium text-red-600">{timeline.delay_days} days</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-slate-600">Confidence</span>
            <span className="font-medium">{Math.round(timeline.confidence * 100)}%</span>
          </div>
        </CardContent>
      </Card>

      {/* Risks */}
      {risks.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              Identified Risks ({risks.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {risks.map((risk, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold capitalize ${severityColors[risk.severity]}`}>
                  {risk.severity}
                </span>
                <p className="text-sm text-slate-700">{risk.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-violet-600" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {suggestions.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500" />
                  {s}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
