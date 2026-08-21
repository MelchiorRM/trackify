import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import {
  CHART_AXIS_LINE_STYLE,
  CHART_LABEL_FILL,
  CHART_TICK_STYLE,
  DOMAIN_CHART_COLORS,
  DOMAIN_LABELS,
  DOMAINS,
} from '@/utils/constants'

export function DomainBreakdown({ totals }) {
  const data = DOMAINS.map((domain) => ({
    domain,
    label: DOMAIN_LABELS[domain],
    count: totals[domain] ?? 0,
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 16, right: 8, left: 0, bottom: 0 }}>
        <XAxis dataKey="label" tickLine={false} axisLine={CHART_AXIS_LINE_STYLE} tick={CHART_TICK_STYLE} />
        <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={CHART_TICK_STYLE} width={28} />
        <Tooltip cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={56}>
          {data.map((entry) => (
            <Cell key={entry.domain} fill={DOMAIN_CHART_COLORS[entry.domain]} />
          ))}
          <LabelList dataKey="count" position="top" fill={CHART_LABEL_FILL} fontSize={12} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
