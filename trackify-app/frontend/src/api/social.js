import { apiClient } from './client'

export const followUser = (username) => apiClient.post(`/follows/${username}`).then((r) => r.data)

export const unfollowUser = (username) => apiClient.delete(`/follows/${username}`).then((r) => r.data)

export const fetchFollowers = (params = {}) =>
  apiClient.get('/follows/followers', { params }).then((r) => r.data)

export const fetchFollowing = (params = {}) =>
  apiClient.get('/follows/following', { params }).then((r) => r.data)

export const fetchFeed = (params = {}) => apiClient.get('/feed', { params }).then((r) => r.data)
