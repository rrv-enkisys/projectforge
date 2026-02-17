import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface Task {
  id: string
  title: string
  description: string
  project_id: string
  milestone_id: string | null
  parent_task_id: string | null
  status: 'todo' | 'in_progress' | 'done'
  priority: 'critical' | 'high' | 'medium' | 'low'
  start_date: string
  due_date: string
  estimated_hours: string | null
  actual_hours: string | null
  position: number
  organization_id: string
  created_at: string
  updated_at: string
}

export interface TaskListResponse {
  data: Task[]
  total: number
  has_more: boolean
}

export interface TaskCreateInput {
  title: string
  description?: string
  project_id: string
  milestone_id?: string | null
  parent_task_id?: string | null
  status?: 'todo' | 'in_progress' | 'done'
  priority?: 'critical' | 'high' | 'medium' | 'low'
  start_date?: string
  due_date: string
  estimated_hours?: number | null
  actual_hours?: number | null
}

export interface TaskUpdateInput extends Partial<TaskCreateInput> {}

export function useTasks(projectId?: string, skip = 0, limit = 100) {
  return useQuery({
    queryKey: ['tasks', projectId, skip, limit],
    queryFn: async () => {
      const params: any = { skip, limit }
      if (projectId) {
        params.project_id = projectId
      }
      const response = await api.get<TaskListResponse>('/api/v1/tasks', { params })
      return response.data
    },
  })
}

export function useCreateTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: TaskCreateInput) => {
      const response = await api.post<Task>('/api/v1/tasks', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export function useUpdateTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TaskUpdateInput }) => {
      const response = await api.patch<Task>(`/api/v1/tasks/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export function useDeleteTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/tasks/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
