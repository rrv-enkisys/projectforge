import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import { api } from '@/lib/api'

export interface ChatSession {
  id: string
  organization_id: string
  user_id: string
  project_id: string | null
  title: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface ChatSessionListResponse {
  data: ChatSession[]
  total: number
}

export interface ChatMessageListResponse {
  data: ChatMessage[]
  total: number
}

export function useChatSessions() {
  return useQuery({
    queryKey: ['chat-sessions'],
    queryFn: async () => {
      const response = await api.get<ChatSessionListResponse>('/api/v1/chat/sessions')
      return response.data
    },
  })
}

export function useChatMessages(sessionId: string | null) {
  return useQuery({
    queryKey: ['chat-messages', sessionId],
    queryFn: async () => {
      const response = await api.get<ChatMessageListResponse>(`/api/v1/chat/sessions/${sessionId}/messages`)
      return response.data
    },
    enabled: !!sessionId,
  })
}

export function useCreateChatSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: { title?: string; project_id?: string }) => {
      const response = await api.post<ChatSession>('/api/v1/chat/sessions', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
    },
  })
}

export function useDeleteChatSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (sessionId: string) => {
      await api.delete(`/api/v1/chat/sessions/${sessionId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
    },
  })
}

export function useSendMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: {
      session_id: string
      content: string
      project_id?: string | null
      organization_id?: string | null
    }) => {
      const response = await api.post<ChatMessage>('/api/v1/chat/messages', data)
      return response.data
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', variables.session_id] })
    },
  })
}

// Hook for streaming messages via SSE
export function useStreamMessage() {
  const [isStreaming, setIsStreaming] = useState(false)

  const stream = useCallback(
    async (
      data: { session_id: string; content: string; project_id?: string | null },
      onChunk: (chunk: string) => void,
      onDone: () => void,
    ) => {
      setIsStreaming(true)
      try {
        const token = await (window as any).__firebaseToken?.()
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        }
        if (token) headers['Authorization'] = `Bearer ${token}`

        const response = await fetch('/api/v1/chat/messages/stream', {
          method: 'POST',
          headers,
          body: JSON.stringify(data),
        })

        if (!response.body) return

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const chunk = line.slice(6)
              if (chunk === '[DONE]') {
                onDone()
              } else {
                onChunk(chunk)
              }
            }
          }
        }
      } finally {
        setIsStreaming(false)
      }
    },
    [],
  )

  return { stream, isStreaming }
}
