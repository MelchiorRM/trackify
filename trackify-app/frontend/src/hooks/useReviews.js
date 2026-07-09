import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createReview, listReviews } from '@/api/reviews'

export function useReviews(itemId) {
  return useQuery({
    queryKey: ['reviews', itemId],
    queryFn: () => listReviews(itemId),
    enabled: Boolean(itemId),
  })
}

export function useCreateReview(itemId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (review) => createReview(review),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reviews', itemId] }),
  })
}
