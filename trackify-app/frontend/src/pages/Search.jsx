import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { DomainTabs } from '@/components/common/DomainTabs'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { MediaGrid } from '@/components/media/MediaGrid'
import { Input } from '@/components/ui/input'
import { useDebounce } from '@/hooks/useDebounce'
import { useAddToLibrary, useLibrary } from '@/hooks/useLibrary'
import { useSearch } from '@/hooks/useSearch'

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const domain = searchParams.get('domain') ?? null
  const debouncedQuery = useDebounce(query, 300)

  const { data, isLoading } = useSearch(debouncedQuery, domain)
  const { data: library } = useLibrary()
  const addToLibrary = useAddToLibrary()

  const isItemInLibrary = (item) =>
    library?.some((entry) => entry.item.domain === item.domain && entry.item.external_id === item.external_id)

  const updateParams = (updates) => {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(updates)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    setSearchParams(next, { replace: true })
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <Input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          updateParams({ q: e.target.value })
        }}
        placeholder="Search movies, books, music..."
        className="mb-4"
        autoFocus
      />
      <DomainTabs value={domain} onChange={(d) => updateParams({ domain: d })} />

      <div className="mt-6">
        {isLoading && <LoadingSpinner className="mx-auto h-8 w-8" />}
        {!isLoading && debouncedQuery && data?.results.length === 0 && (
          <EmptyState title="No results" description={`Nothing matched "${debouncedQuery}"`} />
        )}
        {!isLoading && data?.results.length > 0 && (
          <MediaGrid
            items={data.results}
            onAdd={(item) => addToLibrary.mutate({ domain: item.domain, externalId: item.external_id })}
            isItemInLibrary={isItemInLibrary}
            addingExternalId={addToLibrary.isPending ? addToLibrary.variables?.externalId : null}
          />
        )}
      </div>
    </div>
  )
}
