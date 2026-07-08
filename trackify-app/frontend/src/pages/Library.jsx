import { useState } from 'react'

import { DomainTabs } from '@/components/common/DomainTabs'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { LibraryRow } from '@/components/library/LibraryRow'
import { useLibrary, useRemoveFromLibrary, useUpdateLibraryEntry } from '@/hooks/useLibrary'
import { STATUS_LABELS, STATUSES } from '@/utils/constants'

export default function Library() {
  const [domain, setDomain] = useState(null)
  const [status, setStatus] = useState(null)

  const { data: entries, isLoading } = useLibrary({ domain, status })
  const updateEntry = useUpdateLibraryEntry()
  const removeEntry = useRemoveFromLibrary()

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Your library</h1>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <DomainTabs value={domain} onChange={setDomain} />
        <select
          value={status ?? ''}
          onChange={(e) => setStatus(e.target.value || null)}
          className="h-9 rounded-md border border-input bg-background px-2 text-sm shadow-sm"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <LoadingSpinner className="mx-auto h-8 w-8" />}
      {!isLoading && entries?.length === 0 && (
        <EmptyState title="Your library is empty" description="Search for something to add it here." />
      )}
      {!isLoading && entries?.length > 0 && (
        <div className="space-y-2">
          {entries.map((entry) => (
            <LibraryRow
              key={entry.id}
              entry={entry}
              isUpdating={updateEntry.isPending}
              onStatusChange={(newStatus) =>
                updateEntry.mutate({ libraryId: entry.id, updates: { status: newStatus } })
              }
              onRemove={() => removeEntry.mutate(entry.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
