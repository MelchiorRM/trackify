import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useCollections, useCreateCollection } from '@/hooks/useCollections'
import { useAuthStore } from '@/store/authStore'

function CollectionGrid({ collections }) {
  if (!collections || collections.length === 0) return null
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {collections.map((collection) => (
        <Link key={collection.id} to={`/collections/${collection.id}`}>
          <Card className="h-full transition hover:border-primary">
            <CardContent className="pt-6">
              <p className="font-medium">{collection.name}</p>
              {collection.description && (
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{collection.description}</p>
              )}
              <p className="mt-2 text-xs text-muted-foreground">
                {collection.items.length} item{collection.items.length === 1 ? '' : 's'}
                {!collection.is_public && ' · Private'}
              </p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  )
}

export default function Collections() {
  const user = useAuthStore((s) => s.user)
  const [showForm, setShowForm] = useState(false)
  const { data: myCollections, isLoading: myLoading } = useCollections({ user_id: user?.id })
  const { data: publicCollections, isLoading: publicLoading } = useCollections()
  const createCollection = useCreateCollection()
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting },
  } = useForm()

  const onCreate = async (values) => {
    await createCollection.mutateAsync({ name: values.name, description: values.description || null })
    reset()
    setShowForm(false)
  }

  const otherPublicCollections = publicCollections?.filter((c) => c.user_id !== user?.id) ?? []

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Collections</h1>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cancel' : 'New list'}
        </Button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit(onCreate)} className="space-y-3 rounded-lg border p-4">
          <FormField label="Name" registration={register('name', { required: true })} />
          <FormField label="Description" registration={register('description')} />
          <Button type="submit" size="sm" disabled={isSubmitting}>
            Create list
          </Button>
        </form>
      )}

      <section>
        <h2 className="mb-3 text-lg font-semibold">My lists</h2>
        {myLoading && <LoadingSpinner className="h-6 w-6" />}
        {!myLoading && (myCollections?.length ?? 0) === 0 && (
          <EmptyState title="No lists yet" description="Create one to start curating." />
        )}
        <CollectionGrid collections={myCollections} />
      </section>

      <section>
        {/* No follow graph exists yet (that's Phase 4), so this is every
            public list rather than being scoped to who you follow. */}
        <h2 className="mb-3 text-lg font-semibold">Public lists</h2>
        {publicLoading && <LoadingSpinner className="h-6 w-6" />}
        {!publicLoading && otherPublicCollections.length === 0 && <EmptyState title="No public lists yet" />}
        <CollectionGrid collections={otherPublicCollections} />
      </section>
    </div>
  )
}
