import { DOMAIN_CHART_COLORS, DOMAIN_LABELS, DOMAINS } from '@/utils/constants'

export function GenreCloud({ topGenres }) {
  return (
    <div className="grid gap-6 sm:grid-cols-3">
      {DOMAINS.map((domain) => {
        const genres = topGenres[domain] ?? []
        const max = Math.max(1, ...genres.map((g) => g.count))
        return (
          <div key={domain}>
            <h3 className="mb-2 text-sm font-medium text-muted-foreground">{DOMAIN_LABELS[domain]}</h3>
            {genres.length === 0 ? (
              <p className="text-sm text-muted-foreground">No genres yet.</p>
            ) : (
              <ul className="space-y-1.5">
                {genres.map((g) => (
                  <li key={g.genre} className="flex items-center gap-2">
                    <span className="w-20 flex-shrink-0 truncate text-sm">{g.genre}</span>
                    <span className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                      <span
                        className="block h-full rounded-full"
                        style={{ width: `${(g.count / max) * 100}%`, backgroundColor: DOMAIN_CHART_COLORS[domain] }}
                      />
                    </span>
                    <span className="w-6 flex-shrink-0 text-right text-xs text-muted-foreground">{g.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )
      })}
    </div>
  )
}
