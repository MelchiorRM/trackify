import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { useUpdateFavorites } from '@/hooks/useFavorites'
import { useLibrary } from '@/hooks/useLibrary'

export function FavoritesPicker({ initialItemIds, onDone }) {
  const { data: library } = useLibrary()
  const [selected, setSelected] = useState(initialItemIds)
  const updateFavorites = useUpdateFavorites()

  const toggle = (itemId) => {
    setSelected((prev) => {
      if (prev.includes(itemId)) return prev.filter((id) => id !== itemId)
      if (prev.length >= 4) return prev
      return [...prev, itemId]
    })
  }

  const handleSave = () => {
    updateFavorites.mutate(selected, { onSuccess: onDone })
  }

  return (
    <div className="rounded-lg border p-4">
      <p className="mb-3 text-sm text-muted-foreground">
        Pick up to 4 favorites from your library ({selected.length}/4).
      </p>
      <div className="grid grid-cols-4 gap-3 sm:grid-cols-6">
        {(library ?? []).map((entry) => {
          const isSelected = selected.includes(entry.item.id)
          return (
            <button
              key={entry.id}
              type="button"
              onClick={() => toggle(entry.item.id)}
              disabled={!isSelected && selected.length >= 4}
              className={`relative aspect-[2/3] overflow-hidden rounded-md border-2 ${
                isSelected ? 'border-primary' : 'border-transparent'
              } disabled:opacity-40`}
            >
              {entry.item.cover_url ? (
                <img src={entry.item.cover_url} alt={entry.item.title} className="h-full w-full object-cover" />
              ) : (
                <span className="flex h-full items-center justify-center bg-muted p-1 text-center text-[10px]">
                  {entry.item.title}
                </span>
              )}
            </button>
          )
        })}
      </div>
      <div className="mt-4 flex gap-2">
        <Button size="sm" onClick={handleSave} disabled={updateFavorites.isPending}>
          Save favorites
        </Button>
        <Button size="sm" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
      </div>
    </div>
  )
}
