import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ActivityChart } from '@/components/stats/ActivityChart'
import { DomainBreakdown } from '@/components/stats/DomainBreakdown'
import { GenreCloud } from '@/components/stats/GenreCloud'
import { RatingsDistribution } from '@/components/stats/RatingsDistribution'
import { StatCard } from '@/components/stats/StatCard'
import { useStats } from '@/hooks/useStats'
import { DOMAIN_LABELS, DOMAINS } from '@/utils/constants'
import { formatRating } from '@/utils/formatters'

export default function Stats() {
  const { data: stats, isLoading } = useStats()

  if (isLoading || !stats) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner className="h-8 w-8" />
      </div>
    )
  }

  const totalCompleted = DOMAINS.reduce((sum, domain) => sum + (stats.totals[domain] ?? 0), 0)

  return (
    <div className="mx-auto max-w-4xl space-y-10 px-4 py-8">
      <h1 className="text-2xl font-semibold tracking-tight">Your stats</h1>

      <section className="grid grid-cols-3 gap-4">
        <StatCard label="Total completed" value={totalCompleted} />
        <StatCard label="Completion rate" value={`${Math.round(stats.completion_rate * 100)}%`} />
        <StatCard label="Longest streak" value={`${stats.longest_streak_days}d`} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Completed per domain</h2>
        <DomainBreakdown totals={stats.totals} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Rating &amp; pace per domain</h2>
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th className="px-4 py-2 font-medium">Domain</th>
                <th className="px-4 py-2 font-medium">Avg rating</th>
                <th className="px-4 py-2 font-medium">Pace / month</th>
              </tr>
            </thead>
            <tbody>
              {DOMAINS.map((domain) => (
                <tr key={domain} className="border-t">
                  <td className="px-4 py-2">{DOMAIN_LABELS[domain]}</td>
                  <td className="px-4 py-2">{formatRating(stats.avg_rating_per_domain[domain])}</td>
                  <td className="px-4 py-2">{stats.pace_per_domain[domain].toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Consumption over time</h2>
        {stats.consumption_over_time.length === 0 ? (
          <EmptyState title="No activity yet" description="Complete an item to see your trend here." />
        ) : (
          <ActivityChart data={stats.consumption_over_time} />
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Ratings distribution</h2>
        <RatingsDistribution distribution={stats.ratings_distribution} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Top genres</h2>
        <GenreCloud topGenres={stats.top_genres} />
      </section>
    </div>
  )
}
