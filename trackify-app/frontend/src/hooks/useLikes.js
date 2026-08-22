import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createLike, deleteLike, fetchLikes } from '@/api/likes'

// limit: 100 keeps this a single request for the common case (a toggle
// button showing count + "did I like this") without a dedicated
// is-liked/count endpoint — see LikeButton.jsx.
export function useLikes(targetType, targetId) {
  return useQuery({
    queryKey: ['likes', targetType, targetId],
    queryFn: () => fetchLikes(targetType, targetId, { limit: 100 }),
    enabled: Boolean(targetId),
  })
}

export function useCreateLike(targetType, targetId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => createLike(targetType, targetId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['likes', targetType, targetId] }),
  })
}

export function useDeleteLike(targetType, targetId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => deleteLike(targetType, targetId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['likes', targetType, targetId] }),
  })
}
