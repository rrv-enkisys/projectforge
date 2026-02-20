import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface Document {
  id: string
  project_id: string
  organization_id: string
  name: string
  file_name: string
  file_path: string
  file_type: string
  file_size: number
  chunk_count?: number
  status: 'pending' | 'processing' | 'processed' | 'failed'
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface DocumentListResponse {
  data: Document[]
  total: number
  skip: number
  limit: number
}

export function useDocuments(projectId?: string) {
  return useQuery({
    queryKey: ['documents', projectId],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (projectId) params.project_id = projectId
      const response = await api.get<DocumentListResponse>('/api/v1/documents', { params })
      return response.data
    },
  })
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: async () => {
      const response = await api.get<Document>(`/api/v1/documents/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ file, projectId, name }: { file: File; projectId: string; name?: string }) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('project_id', projectId)
      if (name) formData.append('name', name)

      const response = await api.post<Document>('/api/v1/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/documents/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}
