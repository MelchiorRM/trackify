import { apiClient } from './client'

export const search = (q, domain, page = 1) =>
  apiClient.get('/search', { params: { q, domain, page } }).then((r) => r.data)
