import { apiClient } from './client'

export const createLike = (targetType, targetId) =>
  apiClient.post('/likes', { target_type: targetType, target_id: targetId }).then((r) => r.data)

export const deleteLike = (targetType, targetId) =>
  apiClient
    .delete('/likes', { data: { target_type: targetType, target_id: targetId } })
    .then((r) => r.data)

export const fetchLikes = (targetType, targetId, params = {}) =>
  apiClient
    .get('/likes', { params: { target_type: targetType, target_id: targetId, ...params } })
    .then((r) => r.data)
