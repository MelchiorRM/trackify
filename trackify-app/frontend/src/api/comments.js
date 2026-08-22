import { apiClient } from './client'

export const fetchComments = (targetType, targetId, params = {}) =>
  apiClient.get(`/${targetType}s/${targetId}/comments`, { params }).then((r) => r.data)

export const createComment = (targetType, targetId, body) =>
  apiClient.post(`/${targetType}s/${targetId}/comments`, { body }).then((r) => r.data)

export const updateComment = (commentId, body) =>
  apiClient.patch(`/comments/${commentId}`, { body }).then((r) => r.data)

export const deleteComment = (commentId) =>
  apiClient.delete(`/comments/${commentId}`).then((r) => r.data)
