import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  fetchPublicProfile,
  fetchUserCollections,
  fetchUserDiary,
  fetchUserLibrary,
  fetchUserReviews,
  updateMe,
} from '@/api/users'
import { useAuthStore } from '@/store/authStore'

export function useProfile(username) {
  return useQuery({
    queryKey: ['profile', username],
    queryFn: () => fetchPublicProfile(username),
    enabled: Boolean(username),
  })
}

export function useProfileLibrary(username, params = {}) {
  return useQuery({
    queryKey: ['profile', username, 'library', params],
    queryFn: () => fetchUserLibrary(username, params),
    enabled: Boolean(username),
  })
}

export function useProfileReviews(username) {
  return useQuery({
    queryKey: ['profile', username, 'reviews'],
    queryFn: () => fetchUserReviews(username),
    enabled: Boolean(username),
  })
}

export function useProfileCollections(username) {
  return useQuery({
    queryKey: ['profile', username, 'collections'],
    queryFn: () => fetchUserCollections(username),
    enabled: Boolean(username),
  })
}

export function useProfileDiary(username, params = {}) {
  return useQuery({
    queryKey: ['profile', username, 'diary', params],
    queryFn: () => fetchUserDiary(username, params),
    enabled: Boolean(username),
  })
}

export function useUpdateMe() {
  const queryClient = useQueryClient()
  const setUser = useAuthStore((s) => s.setUser)
  return useMutation({
    mutationFn: (updates) => updateMe(updates),
    onSuccess: (user) => {
      setUser(user)
      queryClient.invalidateQueries({ queryKey: ['profile', user.username] })
    },
  })
}
