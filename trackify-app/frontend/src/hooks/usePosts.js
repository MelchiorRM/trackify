import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createPost, deletePost, fetchPost } from '@/api/posts'
import { fetchUserPosts } from '@/api/users'

export function usePost(postId) {
  return useQuery({
    queryKey: ['posts', postId],
    queryFn: () => fetchPost(postId),
    enabled: Boolean(postId),
  })
}

export function useUserPosts(username, params = {}) {
  return useQuery({
    queryKey: ['profile', username, 'posts', params],
    queryFn: () => fetchUserPosts(username, params),
    enabled: Boolean(username),
  })
}

export function useCreatePost() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body) => createPost(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['feed'] }),
  })
}

export function useDeletePost() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (postId) => deletePost(postId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['feed'] }),
  })
}
