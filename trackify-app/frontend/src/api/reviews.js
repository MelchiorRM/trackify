import { apiClient } from './client'

export const listReviews = (itemId) => apiClient.get('/reviews', { params: { item_id: itemId } }).then((r) => r.data)

export const createReview = (review) => apiClient.post('/reviews', review).then((r) => r.data)
