import { apiClient } from './client'

export const createRepost = (targetType, targetId, comment) =>
  apiClient
    .post('/reposts', { target_type: targetType, target_id: targetId, comment: comment || null })
    .then((r) => r.data)

export const deleteRepost = (repostId) =>
  apiClient.delete(`/reposts/${repostId}`).then((r) => r.data)
