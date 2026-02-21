import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface RAGQueryInput {
  project_id: string
  question: string
  max_chunks?: number
}

interface RAGSource {
  document_id: string
  chunk_id: string
  content: string
  similarity: number
  chunk_index: number
}

interface RAGResponse {
  answer: string
  sources: RAGSource[]
  confidence: 'high' | 'medium' | 'low'
  chunks_retrieved: number
}

export function useRAGQuery() {
  return useMutation({
    mutationFn: async (data: RAGQueryInput) => {
      const response = await api.post<RAGResponse>('/api/v1/rag/query', data)
      return response.data
    },
  })
}
