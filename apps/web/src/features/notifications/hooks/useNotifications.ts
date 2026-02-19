import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface InAppNotification {
  id: string
  organization_id: string
  user_id: string
  event_type: string
  title: string
  body: string
  actor_name: string
  status: 'pending' | 'read'
  created_at: string
  read_at: string | null
}

export interface NotificationListResponse {
  data: InAppNotification[]
  total: number
}

const NOTIF_BASE = '/api/v1/notifications/in-app'

export function useNotifications(unreadOnly = false) {
  return useQuery({
    queryKey: ['notifications', unreadOnly],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (unreadOnly) params.unread_only = 'true'
      const response = await api.get<NotificationListResponse>(NOTIF_BASE, { params })
      return response.data
    },
    // Stop polling if the endpoint returns an error (service not yet deployed)
    refetchInterval: (query) => (query.state.status === 'error' ? false : 30_000),
    retry: false,
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: async () => {
      const response = await api.get<{ unread_count: number }>(`${NOTIF_BASE}/unread-count`)
      return response.data.unread_count
    },
    // Stop polling on error to avoid console spam when service is unavailable
    refetchInterval: (query) => (query.state.status === 'error' ? false : 30_000),
    retry: false,
  })
}

export function useMarkAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`${NOTIF_BASE}/${id}/read`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] })
    },
  })
}

export function useMarkAllAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      await api.patch(`${NOTIF_BASE}/read-all`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] })
    },
  })
}

export function useDeleteNotification() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${NOTIF_BASE}/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] })
    },
  })
}
