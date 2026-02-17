import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface Client {
  id: string
  name: string
  contact_info: Record<string, any>
  settings: Record<string, any>
  organization_id: string
  created_at: string
  updated_at: string
}

export interface ClientListResponse {
  data: Client[]
  total: number
  has_more: boolean
}

export interface ClientCreateInput {
  name: string
  contact_info?: Record<string, any>
  settings?: Record<string, any>
}

export interface ClientUpdateInput extends Partial<ClientCreateInput> {}

export function useClients(skip = 0, limit = 100) {
  return useQuery({
    queryKey: ['clients', skip, limit],
    queryFn: async () => {
      const response = await api.get<ClientListResponse>('/api/v1/clients', {
        params: { skip, limit },
      })
      return response.data
    },
  })
}

export function useCreateClient() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: ClientCreateInput) => {
      const response = await api.post<Client>('/api/v1/clients', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

export function useUpdateClient() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ClientUpdateInput }) => {
      const response = await api.patch<Client>(`/api/v1/clients/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

export function useDeleteClient() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/clients/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}
