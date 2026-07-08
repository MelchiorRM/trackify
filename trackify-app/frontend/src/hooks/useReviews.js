import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createReview, deleteReview, listReviews, updateReview } from '@/api/reviews'

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

export function useUpdateReview(itemId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ reviewId, updates }) => updateReview(reviewId, updates),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reviews', itemId] }),
  })
}

export function useDeleteReview(itemId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (reviewId) => deleteReview(reviewId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reviews', itemId] }),
  })
}
