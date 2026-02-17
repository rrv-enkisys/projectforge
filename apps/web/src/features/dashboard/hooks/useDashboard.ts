import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { DashboardStatsResponse } from '../types'

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      const response = await api.get<DashboardStatsResponse>('/api/v1/dashboard/stats')
      return response.data.data
    },
    refetchInterval: 60000, // Refresh every minute
  })
}
