import { useQuery } from '@tanstack/react-query'

import { getItem } from '@/api/items'

export function useItem(domain, externalId) {
  return useQuery({
    queryKey: ['item', domain, externalId],
    queryFn: () => getItem(domain, externalId),
    enabled: Boolean(domain && externalId),
  })
}
