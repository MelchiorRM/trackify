import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  fetchNotifications,
  fetchUnreadNotificationCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/api/notifications'

export function useNotifications(params = {}) {
  return useQuery({ queryKey: ['notifications', params], queryFn: () => fetchNotifications(params) })
}

// Polling, not push (see appPlan.txt WHAT THIS PLAN DOES NOT COVER —
// real-time delivery is deferred).
export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: fetchUnreadNotificationCount,
    refetchInterval: 30_000,
  })
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (notificationId) => markNotificationRead(notificationId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })
}
