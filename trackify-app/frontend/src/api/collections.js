import { apiClient } from './client'

export const listCollections = (params = {}) => apiClient.get('/collections', { params }).then((r) => r.data)

export const createCollection = (collection) => apiClient.post('/collections', collection).then((r) => r.data)

export const getCollection = (collectionId) => apiClient.get(`/collections/${collectionId}`).then((r) => r.data)

export const updateCollection = (collectionId, updates) =>
  apiClient.patch(`/collections/${collectionId}`, updates).then((r) => r.data)

export const deleteCollection = (collectionId) =>
  apiClient.delete(`/collections/${collectionId}`).then((r) => r.data)

export const addCollectionItem = (collectionId, { domain, externalId, note }) =>
  apiClient
    .post(`/collections/${collectionId}/items`, { domain, external_id: externalId, note })
    .then((r) => r.data)

export const removeCollectionItem = (collectionId, itemId) =>
  apiClient.delete(`/collections/${collectionId}/items/${itemId}`).then((r) => r.data)
