import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { ProjectListResponse } from '../types'

export function useProjects(skip = 0, limit = 20) {
  return useQuery({
    queryKey: ['projects', skip, limit],
    queryFn: async () => {
      const response = await api.get<ProjectListResponse>('/api/v1/projects', {
        params: { skip, limit },
      })
      return response.data
    },
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/projects/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}
