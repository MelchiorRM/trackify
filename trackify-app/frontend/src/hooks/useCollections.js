import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  addCollectionItem,
  createCollection,
  deleteCollection,
  getCollection,
  listCollections,
  removeCollectionItem,
  updateCollection,
} from '@/api/collections'

export function useCollections(params = {}) {
  return useQuery({ queryKey: ['collections', 'list', params], queryFn: () => listCollections(params) })
}

export function useCollection(collectionId) {
  return useQuery({
    queryKey: ['collections', collectionId],
    queryFn: () => getCollection(collectionId),
    enabled: Boolean(collectionId),
  })
}

export function useCreateCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (collection) => createCollection(collection),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections', 'list'] }),
  })
}

export function useUpdateCollection(collectionId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (updates) => updateCollection(collectionId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections', collectionId] })
      queryClient.invalidateQueries({ queryKey: ['collections', 'list'] })
    },
  })
}

export function useDeleteCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (collectionId) => deleteCollection(collectionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections', 'list'] }),
  })
}

export function useAddCollectionItem(collectionId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (item) => addCollectionItem(collectionId, item),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections', collectionId] }),
  })
}

export function useRemoveCollectionItem(collectionId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemId) => removeCollectionItem(collectionId, itemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections', collectionId] }),
  })
}
