import { useQuery } from '@tanstack/react-query'

import { search } from '@/api/search'

export function useSearch(query, domain) {
  return useQuery({
    queryKey: ['search', query, domain],
    queryFn: () => search(query, domain),
    enabled: query.trim().length > 0,
  })
}
