import { apiClient } from './client'

export const listDiaryEntries = (libraryId) => apiClient.get(`/library/${libraryId}/diary`).then((r) => r.data)

export const logDiaryEntry = (libraryId, entry) =>
  apiClient.post(`/library/${libraryId}/diary`, entry).then((r) => r.data)

export const deleteDiaryEntry = (entryId) => apiClient.delete(`/diary/${entryId}`).then((r) => r.data)
