import { Star } from 'lucide-react'
import { useState } from 'react'

import { cn } from '@/lib/utils'

export function StarRating({ value = 0, onChange, readOnly = false, size = 20 }) {
  const [hoverValue, setHoverValue] = useState(null)
  const display = hoverValue ?? value

  const handleClick = (starIndex, half) => {
    if (readOnly) return
    onChange?.(starIndex + (half ? 0.5 : 1))
  }

  return (
    <div className={cn('flex items-center gap-0.5', readOnly && 'pointer-events-none')}>
      {[0, 1, 2, 3, 4].map((starIndex) => {
        const fillPct = Math.max(0, Math.min(1, display - starIndex)) * 100
        return (
          <div
            key={starIndex}
            className="relative"
            style={{ width: size, height: size }}
            onMouseLeave={() => setHoverValue(null)}
          >
            <Star className="absolute inset-0 text-muted-foreground" style={{ width: size, height: size }} />
            <div className="absolute inset-0 overflow-hidden" style={{ width: `${fillPct}%` }}>
              <Star className="fill-primary text-primary" style={{ width: size, height: size }} />
            </div>
            {!readOnly && (
              <>
                <button
                  type="button"
                  className="absolute inset-y-0 left-0 w-1/2"
                  onMouseEnter={() => setHoverValue(starIndex + 0.5)}
                  onClick={() => handleClick(starIndex, true)}
                  aria-label={`Rate ${starIndex + 0.5} stars`}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 w-1/2"
                  onMouseEnter={() => setHoverValue(starIndex + 1)}
                  onClick={() => handleClick(starIndex, false)}
                  aria-label={`Rate ${starIndex + 1} stars`}
                />
              </>
            )}
          </div>
        )
      })}
      {value > 0 && <span className="ml-1.5 text-sm text-muted-foreground">{display.toFixed(1)}</span>}
    </div>
  )
}
