import { useMutation, useQueryClient } from '@tanstack/react-query'

import { createRepost, deleteRepost } from '@/api/reposts'

export function useCreateRepost(targetType, targetId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (comment) => createRepost(targetType, targetId, comment),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['feed'] }),
  })
}

export function useDeleteRepost() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (repostId) => deleteRepost(repostId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['feed'] }),
  })
}
