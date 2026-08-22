import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createComment, deleteComment, fetchComments, updateComment } from '@/api/comments'

export function useComments(targetType, targetId) {
  return useQuery({
    queryKey: ['comments', targetType, targetId],
    queryFn: () => fetchComments(targetType, targetId),
    enabled: Boolean(targetId),
  })
}

export function useCreateComment(targetType, targetId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body) => createComment(targetType, targetId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['comments', targetType, targetId] }),
  })
}

export function useUpdateComment(targetType, targetId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ commentId, body }) => updateComment(commentId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['comments', targetType, targetId] }),
  })
}

export function useDeleteComment(targetType, targetId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (commentId) => deleteComment(commentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['comments', targetType, targetId] }),
  })
}
