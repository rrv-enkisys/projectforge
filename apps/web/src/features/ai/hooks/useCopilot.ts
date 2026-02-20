import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface ProjectAnalysis {
  health: {
    status: 'healthy' | 'at_risk' | 'critical' | 'unknown'
    score: number
    message: string
  }
  risks: Array<{
    type: string
    severity: 'low' | 'medium' | 'high'
    description: string
  }>
  suggestions: string[]
  timeline: {
    predicted_completion: string | null
    confidence: number
    on_track: boolean
    delay_days: number
  }
  metrics: {
    total_tasks: number
    completed_tasks: number
    overdue_tasks: number
    completion_rate: number
    total_milestones: number
    completed_milestones: number
  }
  timestamp: string
}

interface RawProjectAnalysis {
  health: {
    score: number
    status: 'healthy' | 'at_risk' | 'critical' | 'unknown'
    issues: string[]
    task_completion_rate: number
    overdue_tasks_count: number
    overdue_milestones_count: number
  }
  risks: Array<{ type: string; severity: 'low' | 'medium' | 'high'; description: string }>
  completion_prediction: {
    predicted_date: string | null
    confidence: 'low' | 'medium' | 'high'
    estimated_days_remaining: number | null
    completion_rate: number | null
    reasoning: string
  }
  ai_insights: string
  timestamp: string
}

const confidenceMap: Record<string, number> = { low: 0.3, medium: 0.6, high: 0.9 }

function transformAnalysis(raw: RawProjectAnalysis): ProjectAnalysis {
  const cp = raw.completion_prediction ?? {}
  const suggestions = raw.ai_insights
    ? raw.ai_insights
        .split('\n')
        .map((s) => s.replace(/^[\*\-\d\.]+\s*/, '').replace(/\*+/g, '').trim())
        .filter((s) => s.length > 15 && !s.startsWith('#'))
        .slice(0, 5)
    : []

  return {
    health: {
      status: raw.health.status,
      score: raw.health.score,
      message:
        raw.health.issues?.length > 0
          ? raw.health.issues.join('. ')
          : `Project health score: ${raw.health.score}/100`,
    },
    risks: raw.risks || [],
    suggestions,
    timeline: {
      predicted_completion: cp.predicted_date ?? null,
      confidence: confidenceMap[cp.confidence ?? 'low'] ?? 0.3,
      on_track: (cp.estimated_days_remaining ?? 0) <= 0,
      delay_days: Math.max(0, cp.estimated_days_remaining ?? 0),
    },
    metrics: {
      total_tasks: 0,
      completed_tasks: 0,
      overdue_tasks: raw.health.overdue_tasks_count ?? 0,
      completion_rate: raw.health.task_completion_rate ?? 0,
      total_milestones: 0,
      completed_milestones: 0,
    },
    timestamp: raw.timestamp,
  }
}

export function useAnalyzeProject() {
  return useMutation({
    mutationFn: async (projectId: string) => {
      const response = await api.post<RawProjectAnalysis>('/api/v1/copilot/analyze', {
        project_id: projectId,
      })
      return transformAnalysis(response.data)
    },
  })
}

export function useAskCopilot() {
  return useMutation({
    mutationFn: async (data: { project_id: string; question: string }) => {
      const response = await api.post<{ answer: string; context_used: boolean }>(
        '/api/v1/copilot/ask',
        data,
      )
      return response.data
    },
  })
}
