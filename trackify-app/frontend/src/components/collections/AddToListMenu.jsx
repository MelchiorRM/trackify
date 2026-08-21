import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { useAddCollectionItem, useCollections } from '@/hooks/useCollections'
import { useAuthStore } from '@/store/authStore'

export function AddToListMenu({ domain, externalId }) {
  const user = useAuthStore((s) => s.user)
  const { data: collections } = useCollections({ user_id: user?.id })
  const [selectedId, setSelectedId] = useState('')
  const [added, setAdded] = useState(false)
  const addItem = useAddCollectionItem(selectedId || undefined)

  if (!collections || collections.length === 0) {
    return null
  }

  const handleAdd = () => {
    if (!selectedId) return
    addItem.mutate({ domain, externalId }, { onSuccess: () => setAdded(true) })
  }

  return (
    <div className="flex items-center gap-2">
      <select
        value={selectedId}
        onChange={(e) => {
          setSelectedId(e.target.value)
          setAdded(false)
        }}
        className="h-9 rounded-md border border-input bg-background px-2 text-sm shadow-sm"
      >
        <option value="">Add to a list...</option>
        {collections.map((collection) => (
          <option key={collection.id} value={collection.id}>
            {collection.name}
          </option>
        ))}
      </select>
      <Button size="sm" variant="outline" disabled={!selectedId || addItem.isPending} onClick={handleAdd}>
        {added ? 'Added' : 'Add'}
      </Button>
    </div>
  )
}
