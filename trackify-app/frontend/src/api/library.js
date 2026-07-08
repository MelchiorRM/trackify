import { apiClient } from './client'

export const listLibrary = (params = {}) => apiClient.get('/library', { params }).then((r) => r.data)

export const addToLibrary = (domain, externalId) =>
  apiClient.post('/library', { domain, external_id: externalId }).then((r) => r.data)

export const updateLibraryEntry = (libraryId, updates) =>
  apiClient.patch(`/library/${libraryId}`, updates).then((r) => r.data)

export const removeFromLibrary = (libraryId) => apiClient.delete(`/library/${libraryId}`).then((r) => r.data)
