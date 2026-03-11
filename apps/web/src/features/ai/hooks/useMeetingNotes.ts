import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface ActionItem {
  description: string
  assignee_hint: string | null
  due_date_hint: string | null
  priority: 'low' | 'medium' | 'high' | 'urgent'
  context: string | null
}

export interface Decision {
  description: string
  made_by_hint: string | null
  context: string | null
}

export interface FollowUp {
  description: string
  owner_hint: string | null
}

export interface MeetingAnalysis {
  summary: string
  action_items: ActionItem[]
  decisions: Decision[]
  follow_ups: FollowUp[]
  participants_detected: string[]
  meeting_date_hint: string | null
  confidence: number
  warnings: string[]
}

export interface MeetingNotesParseResponse {
  analysis: MeetingAnalysis
  raw_text_length: number
  source_type: 'text' | 'file'
}

export function useAnalyzeMeetingNotes() {
  return useMutation({
    mutationFn: async (input: File | string): Promise<MeetingNotesParseResponse> => {
      const formData = new FormData()
      if (input instanceof File) {
        formData.append('file', input)
      } else {
        formData.append('text', input)
      }
      const response = await api.post<MeetingNotesParseResponse>(
        '/api/v1/agents/meeting/analyze',
        formData,
      )
      return response.data
    },
  })
}
