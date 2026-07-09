import { Badge } from '@/components/ui/badge'

import { DomainBadge } from './DomainBadge'

export function MediaBanner({ item }) {
  return (
    <div className="flex flex-col gap-6 sm:flex-row">
      <div className="flex aspect-[2/3] w-full max-w-[220px] flex-shrink-0 items-center justify-center overflow-hidden rounded-lg bg-muted">
        {item.cover_url ? (
          <img src={item.cover_url} alt={item.title} className="h-full w-full object-cover" />
        ) : (
          <span className="text-sm text-muted-foreground">No cover</span>
        )}
      </div>
      <div className="flex flex-col gap-3">
        <DomainBadge domain={item.domain} className="self-start" />
        <h1 className="text-3xl font-bold tracking-tight">{item.title}</h1>
        <p className="text-muted-foreground">{[item.creator, item.year].filter(Boolean).join(' · ')}</p>
        {item.genres?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {item.genres.map((genre) => (
              <Badge key={genre} variant="outline">
                {genre}
              </Badge>
            ))}
          </div>
        )}
        {item.overview && <p className="max-w-2xl text-sm leading-relaxed">{item.overview}</p>}
        {item.external_url && (
          <a
            href={item.external_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-primary underline-offset-4 hover:underline"
          >
            View on source site ↗
          </a>
        )}
      </div>
    </div>
  )
}
