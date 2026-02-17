import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { ProjectListResponse, Project } from '../types'

export interface ProjectCreateInput {
  name: string
  description?: string
  client_id?: string | null
  start_date: string
  end_date?: string | null
  status?: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled'
  budget?: number | null
}

export interface ProjectUpdateInput extends Partial<ProjectCreateInput> {}

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

export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: ProjectCreateInput) => {
      const response = await api.post<Project>('/api/v1/projects', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ProjectUpdateInput }) => {
      const response = await api.patch<Project>(`/api/v1/projects/${id}`, data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['project', data.id] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/projects/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}
