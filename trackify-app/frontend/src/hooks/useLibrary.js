import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { addToLibrary, listLibrary, removeFromLibrary, updateLibraryEntry } from '@/api/library'

export function useLibrary(params = {}) {
  return useQuery({
    queryKey: ['library', params],
    queryFn: () => listLibrary(params),
  })
}

export function useAddToLibrary() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ domain, externalId }) => addToLibrary(domain, externalId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['library'] }),
  })
}

export function useUpdateLibraryEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ libraryId, updates }) => updateLibraryEntry(libraryId, updates),
    // A status change to "completed" auto-logs a diary entry server-side
    // (see library_service.apply_updates) — invalidate diary too, not just
    // library, or the new entry won't show up without a manual refresh.
    onSuccess: (_data, { libraryId }) => {
      queryClient.invalidateQueries({ queryKey: ['library'] })
      queryClient.invalidateQueries({ queryKey: ['diary', libraryId] })
    },
  })
}

export function useRemoveFromLibrary() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (libraryId) => removeFromLibrary(libraryId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['library'] }),
  })
}
