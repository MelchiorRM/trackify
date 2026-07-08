import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { deleteDiaryEntry, listDiaryEntries, logDiaryEntry } from '@/api/diary'

export function useDiary(libraryId) {
  return useQuery({
    queryKey: ['diary', libraryId],
    queryFn: () => listDiaryEntries(libraryId),
    enabled: Boolean(libraryId),
  })
}

export function useLogDiaryEntry(libraryId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (entry) => logDiaryEntry(libraryId, entry),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['diary', libraryId] }),
  })
}

export function useDeleteDiaryEntry(libraryId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (entryId) => deleteDiaryEntry(entryId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['diary', libraryId] }),
  })
}
