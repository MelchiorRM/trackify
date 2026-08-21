import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import {
  CHART_AXIS_LINE_STYLE,
  CHART_TICK_STYLE,
  DOMAIN_CHART_COLORS,
  DOMAIN_LABELS,
  DOMAINS,
} from '@/utils/constants'
import { formatMonth } from '@/utils/formatters'

export function ActivityChart({ data }) {
  const chartData = data.map((bucket) => ({ ...bucket, monthLabel: formatMonth(bucket.month) }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="#e1e0d9" />
        <XAxis dataKey="monthLabel" tickLine={false} axisLine={CHART_AXIS_LINE_STYLE} tick={CHART_TICK_STYLE} />
        <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={CHART_TICK_STYLE} width={28} />
        <Tooltip />
        <Legend formatter={(value) => DOMAIN_LABELS[value] ?? value} wrapperStyle={{ fontSize: 12 }} />
        {DOMAINS.map((domain) => (
          <Line
            key={domain}
            type="monotone"
            dataKey={domain}
            name={domain}
            stroke={DOMAIN_CHART_COLORS[domain]}
            strokeWidth={2}
            dot={{ r: 4, strokeWidth: 2, stroke: '#fcfcfb' }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
