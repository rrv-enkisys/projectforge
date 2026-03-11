import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface SOWProjectSuggestion {
  name: string
  description: string
  estimated_duration_days: number | null
  estimated_budget: number | null
  currency: string
}

export interface SOWMilestoneSuggestion {
  title: string
  description: string
  target_date_offset_days: number | null
}

export interface SOWTaskSuggestion {
  title: string
  description: string
  estimated_hours: number | null
  priority: 'low' | 'medium' | 'high' | 'urgent'
  milestone_index: number | null
}

export interface SOWSection {
  name: string
  content: string
  confidence: number
}

export interface SOWParseResponse {
  project: SOWProjectSuggestion
  milestones: SOWMilestoneSuggestion[]
  tasks: SOWTaskSuggestion[]
  raw_sections: SOWSection[]
  confidence: number
  warnings: string[]
}

export function useParseSOW() {
  return useMutation({
    mutationFn: async (file: File): Promise<SOWParseResponse> => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post<SOWParseResponse>(
        '/api/v1/agents/sow/parse',
        formData,
      )
      return response.data
    },
  })
}
