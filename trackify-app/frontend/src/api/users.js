import { apiClient } from './client'

export const updateMe = (updates) => apiClient.patch('/users/me', updates).then((r) => r.data)

export const fetchPublicProfile = (username) => apiClient.get(`/users/${username}`).then((r) => r.data)

export const fetchUserLibrary = (username, params = {}) =>
  apiClient.get(`/users/${username}/library`, { params }).then((r) => r.data)

export const fetchUserReviews = (username) => apiClient.get(`/users/${username}/reviews`).then((r) => r.data)

export const fetchUserCollections = (username) =>
  apiClient.get(`/users/${username}/collections`).then((r) => r.data)

export const fetchUserDiary = (username, params = {}) =>
  apiClient.get(`/users/${username}/diary`, { params }).then((r) => r.data)
