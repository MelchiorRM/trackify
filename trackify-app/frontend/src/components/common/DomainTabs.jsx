import { cn } from '@/lib/utils'
import { DOMAINS, DOMAIN_LABELS } from '@/utils/constants'

export function DomainTabs({ value, onChange }) {
  const options = [{ key: null, label: 'All' }, ...DOMAINS.map((d) => ({ key: d, label: DOMAIN_LABELS[d] }))]

  return (
    <div className="flex gap-2">
      {options.map((opt) => (
        <button
          key={opt.label}
          type="button"
          onClick={() => onChange(opt.key)}
          className={cn(
            'rounded-full px-3 py-1 text-sm transition-colors',
            value === opt.key
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
