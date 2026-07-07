import { apiClient } from './client'

export const register = (payload) => apiClient.post('/auth/register', payload).then((r) => r.data)
export const login = (payload) => apiClient.post('/auth/login', payload).then((r) => r.data)
export const logout = () => apiClient.post('/auth/logout').then((r) => r.data)
export const fetchMe = () => apiClient.get('/users/me').then((r) => r.data)
