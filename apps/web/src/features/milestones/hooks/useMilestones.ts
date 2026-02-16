import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface Milestone {
  id: string
  name: string
  description: string | null
  project_id: string
  target_date: string | null
  completed_date: string | null
  status: 'not_started' | 'in_progress' | 'completed'
  organization_id: string
  created_at: string
  updated_at: string
}

export interface MilestoneCreateInput {
  name: string
  description?: string
  project_id: string
  target_date?: string
  status?: 'not_started' | 'in_progress' | 'completed'
}

export interface MilestoneUpdateInput {
  name?: string
  description?: string
  project_id?: string
  target_date?: string
  status?: 'not_started' | 'in_progress' | 'completed'
  completed_date?: string
}

export function useMilestones(projectId?: string) {
  return useQuery({
    queryKey: ['milestones', projectId],
    queryFn: async () => {
      const params = projectId ? { project_id: projectId } : {}
      const response = await api.get('/api/v1/milestones', { params })
      return response.data.data as Milestone[]
    },
  })
}

export function useMilestone(id: string) {
  return useQuery({
    queryKey: ['milestones', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/milestones/${id}`)
      return response.data as Milestone
    },
    enabled: !!id,
  })
}

export function useCreateMilestone() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: MilestoneCreateInput) => {
      const response = await api.post('/api/v1/milestones', data)
      return response.data as Milestone
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones'] })
    },
  })
}

export function useUpdateMilestone() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: MilestoneUpdateInput }) => {
      const response = await api.patch(`/api/v1/milestones/${id}`, data)
      return response.data as Milestone
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones'] })
    },
  })
}

export function useDeleteMilestone() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/milestones/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones'] })
    },
  })
}
