import { apiClient } from './client'

export const fetchNotifications = (params = {}) =>
  apiClient.get('/notifications', { params }).then((r) => r.data)

export const fetchUnreadNotificationCount = () =>
  apiClient.get('/notifications/unread-count').then((r) => r.data)

export const markNotificationRead = (notificationId) =>
  apiClient.patch(`/notifications/${notificationId}/read`).then((r) => r.data)

export const markAllNotificationsRead = () =>
  apiClient.post('/notifications/read-all').then((r) => r.data)
