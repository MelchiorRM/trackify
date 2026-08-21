import { useQuery } from '@tanstack/react-query'

import { fetchMyStats } from '@/api/stats'

export function useStats() {
  return useQuery({ queryKey: ['stats', 'me'], queryFn: fetchMyStats })
}
