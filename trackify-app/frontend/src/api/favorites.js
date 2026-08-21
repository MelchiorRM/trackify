import { apiClient } from './client'

export const updateFavorites = (itemIds) =>
  apiClient.put('/users/me/favorites', { item_ids: itemIds }).then((r) => r.data)
