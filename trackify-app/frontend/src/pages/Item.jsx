import { useParams } from 'react-router-dom'

import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { DiaryEntryForm } from '@/components/library/DiaryEntryForm'
import { DiaryList } from '@/components/library/DiaryList'
import { ProgressBar } from '@/components/library/ProgressBar'
import { StatusPicker } from '@/components/library/StatusPicker'
import { MediaBanner } from '@/components/media/MediaBanner'
import { ReviewCard } from '@/components/reviews/ReviewCard'
import { ReviewForm } from '@/components/reviews/ReviewForm'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useDiary, useLogDiaryEntry } from '@/hooks/useDiary'
import { useItem } from '@/hooks/useItem'
import { useAddToLibrary, useLibrary, useUpdateLibraryEntry } from '@/hooks/useLibrary'
import { useCreateReview, useReviews } from '@/hooks/useReviews'
import { useAuthStore } from '@/store/authStore'

export default function Item() {
  const { domain, externalId } = useParams()
  const { data: item, isLoading } = useItem(domain, externalId)
  const { data: library } = useLibrary()
  const user = useAuthStore((s) => s.user)

  const addToLibrary = useAddToLibrary()
  const updateLibraryEntry = useUpdateLibraryEntry()

  const libraryEntry = library?.find(
    (entry) => entry.item.domain === domain && entry.item.external_id === externalId,
  )

  const { data: diaryEntries } = useDiary(libraryEntry?.id)
  const logDiaryEntry = useLogDiaryEntry(libraryEntry?.id)

  const { data: reviews } = useReviews(item?.id)
  const createReview = useCreateReview(item?.id)
  const myReview = reviews?.find((r) => r.user_id === user?.id)
  const otherReviews = reviews?.filter((r) => r.user_id !== user?.id) ?? []

  if (isLoading || !item) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner className="h-8 w-8" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      <MediaBanner item={item} />

      <Card>
        <CardContent className="flex flex-wrap items-center gap-4 pt-6">
          {libraryEntry ? (
            <>
              <StatusPicker
                value={libraryEntry.status}
                disabled={updateLibraryEntry.isPending}
                onChange={(status) =>
                  updateLibraryEntry.mutate({ libraryId: libraryEntry.id, updates: { status } })
                }
              />
              {libraryEntry.progress_total != null && (
                <div className="w-48">
                  <ProgressBar progress={libraryEntry.progress} total={libraryEntry.progress_total} />
                </div>
              )}
            </>
          ) : (
            <Button onClick={() => addToLibrary.mutate({ domain, externalId })} disabled={addToLibrary.isPending}>
              Add to library
            </Button>
          )}
        </CardContent>
      </Card>

      {libraryEntry && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Diary</h2>
          <DiaryEntryForm isSubmitting={logDiaryEntry.isPending} onSubmit={(entry) => logDiaryEntry.mutate(entry)} />
          <DiaryList entries={diaryEntries ?? []} />
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Your review</h2>
        {myReview ? (
          <ReviewCard review={myReview} />
        ) : (
          <ReviewForm
            isSubmitting={createReview.isPending}
            onSubmit={(review) => createReview.mutate({ item_id: item.id, ...review })}
          />
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Reviews</h2>
        {otherReviews.length ? (
          otherReviews.map((r) => <ReviewCard key={r.id} review={r} />)
        ) : (
          <p className="text-sm text-muted-foreground">No reviews yet.</p>
        )}
      </section>
    </div>
  )
}
