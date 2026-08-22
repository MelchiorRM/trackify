import { apiClient } from './client'

export const startConversation = (username) =>
  apiClient.post(`/conversations/${username}`).then((r) => r.data)

export const fetchConversations = (params = {}) =>
  apiClient.get('/conversations', { params }).then((r) => r.data)

export const fetchUnreadMessageCount = () =>
  apiClient.get('/conversations/unread-count').then((r) => r.data)

export const fetchMessages = (conversationId, params = {}) =>
  apiClient.get(`/conversations/${conversationId}/messages`, { params }).then((r) => r.data)

export const sendMessage = (conversationId, body) =>
  apiClient.post(`/conversations/${conversationId}/messages`, { body }).then((r) => r.data)

export const markConversationRead = (conversationId) =>
  apiClient.post(`/conversations/${conversationId}/read`).then((r) => r.data)
