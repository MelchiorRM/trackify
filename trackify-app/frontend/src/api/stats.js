import { apiClient } from './client'

export const fetchMyStats = () => apiClient.get('/stats/me').then((r) => r.data)
