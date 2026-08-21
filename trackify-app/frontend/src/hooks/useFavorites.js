import { useMutation, useQueryClient } from '@tanstack/react-query'

import { updateFavorites } from '@/api/favorites'

export function useUpdateFavorites() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemIds) => updateFavorites(itemIds),
    // Favorites are keyed under ['profile', username] — invalidate the
    // whole 'profile' prefix rather than threading the username through,
    // since this mutation only ever affects the current user's own profile.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
  })
}
