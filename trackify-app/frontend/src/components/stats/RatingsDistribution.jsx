import { Bar, BarChart, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { CHART_AXIS_LINE_STYLE, CHART_LABEL_FILL, CHART_TICK_STYLE } from '@/utils/constants'

const STARS = [1, 2, 3, 4, 5]

export function RatingsDistribution({ distribution }) {
  const data = STARS.map((star) => ({ star: `${star}★`, count: distribution[star] ?? 0 }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 16, right: 8, left: 0, bottom: 0 }}>
        <XAxis dataKey="star" tickLine={false} axisLine={CHART_AXIS_LINE_STYLE} tick={CHART_TICK_STYLE} />
        <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={CHART_TICK_STYLE} width={28} />
        <Tooltip cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="count" fill="#2a78d6" radius={[4, 4, 0, 0]} maxBarSize={40}>
          <LabelList dataKey="count" position="top" fill={CHART_LABEL_FILL} fontSize={12} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
