import { Link, useNavigate, useParams } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { DomainBadge } from '@/components/media/DomainBadge'
import { Button } from '@/components/ui/button'
import { useCollection, useDeleteCollection, useRemoveCollectionItem, useUpdateCollection } from '@/hooks/useCollections'
import { useAuthStore } from '@/store/authStore'

export default function CollectionDetail() {
  const { collectionId } = useParams()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)

  const { data: collection, isLoading } = useCollection(collectionId)
  const removeItem = useRemoveCollectionItem(collectionId)
  const updateCollection = useUpdateCollection(collectionId)
  const deleteCollection = useDeleteCollection()

  if (isLoading || !collection) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner className="h-8 w-8" />
      </div>
    )
  }

  const isOwner = collection.user_id === user?.id

  const handleDelete = async () => {
    await deleteCollection.mutateAsync(collectionId)
    navigate('/collections')
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{collection.name}</h1>
          {collection.description && <p className="mt-1 text-muted-foreground">{collection.description}</p>}
          {!collection.is_public && <p className="mt-1 text-xs text-muted-foreground">Private list</p>}
        </div>
        {isOwner && (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={updateCollection.isPending}
              onClick={() => updateCollection.mutate({ is_public: !collection.is_public })}
            >
              {collection.is_public ? 'Make private' : 'Make public'}
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="text-destructive hover:text-destructive"
              disabled={deleteCollection.isPending}
              onClick={handleDelete}
            >
              Delete list
            </Button>
          </div>
        )}
      </div>

      {collection.items.length === 0 ? (
        <EmptyState title="No items yet" description="Add items to this list from an item's detail page." />
      ) : (
        <div className="space-y-2">
          {collection.items.map((entry) => (
            <div key={entry.id} className="flex items-center gap-3 rounded-lg border p-3">
              <DomainBadge domain={entry.item.domain} />
              <Link
                to={`/item/${entry.item.domain}/${entry.item.external_id}`}
                className="flex-1 truncate font-medium hover:underline"
              >
                {entry.item.title}
              </Link>
              {entry.note && <span className="text-sm text-muted-foreground">{entry.note}</span>}
              {isOwner && (
                <Button size="sm" variant="ghost" onClick={() => removeItem.mutate(entry.item.id)}>
                  Remove
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
