import { apiClient } from './client'

export const createPost = (body) => apiClient.post('/posts', { body }).then((r) => r.data)

export const fetchPost = (postId) => apiClient.get(`/posts/${postId}`).then((r) => r.data)

export const deletePost = (postId) => apiClient.delete(`/posts/${postId}`).then((r) => r.data)
