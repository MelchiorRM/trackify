import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchFeed, fetchFollowers, fetchFollowing, followUser, unfollowUser } from '@/api/social'

export function useFollow() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (username) => followUser(username),
    onSuccess: (_data, username) => {
      queryClient.invalidateQueries({ queryKey: ['profile', username] })
      queryClient.invalidateQueries({ queryKey: ['social'] })
      queryClient.invalidateQueries({ queryKey: ['feed'] })
    },
  })
}

export function useUnfollow() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (username) => unfollowUser(username),
    onSuccess: (_data, username) => {
      queryClient.invalidateQueries({ queryKey: ['profile', username] })
      queryClient.invalidateQueries({ queryKey: ['social'] })
      queryClient.invalidateQueries({ queryKey: ['feed'] })
    },
  })
}

export function useFollowers(params = {}) {
  return useQuery({ queryKey: ['social', 'followers', params], queryFn: () => fetchFollowers(params) })
}

export function useFollowing(params = {}) {
  return useQuery({ queryKey: ['social', 'following', params], queryFn: () => fetchFollowing(params) })
}

export function useFeed(params = {}) {
  return useQuery({ queryKey: ['feed', params], queryFn: () => fetchFeed(params) })
}
