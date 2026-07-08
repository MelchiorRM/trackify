import { apiClient } from './client'

export const getItem = (domain, externalId) =>
  apiClient.get(`/items/${domain}/${externalId}`).then((r) => r.data)
