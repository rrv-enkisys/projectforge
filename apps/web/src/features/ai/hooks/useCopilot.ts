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

export function useAnalyzeProject() {
  return useMutation({
    mutationFn: async (projectId: string) => {
      const response = await api.post<ProjectAnalysis>('/api/v1/copilot/analyze', {
        project_id: projectId,
      })
      return response.data
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
