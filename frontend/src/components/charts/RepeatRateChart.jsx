import Chart from 'react-apexcharts'
import { fmt } from '../../utils/formatters.js'
import { BASE, TOOLTIP, GRID, AXIS } from './chartDefaults.js'

export default function RepeatRateChart({ data = [] }) {
  const categories  = data.map((d) => fmt.month(d.month))
  const rateData    = data.map((d) => +parseFloat(d.repeat_order_rate_pct || 0).toFixed(1))
  const newData     = data.map((d) => d.new_customers || 0)
  const retData     = data.map((d) => d.repeat_customers || 0)

  const options = {
    chart: { ...BASE, type: 'line', id: 'repeat' },
    colors: ['#7c3aed', '#10b981', '#06b6d4'],
    stroke: { curve: 'smooth', width: [3, 0, 0] },
    fill:   { opacity: [1, 0.85, 0.85], type: ['solid', 'solid', 'solid'] },
    dataLabels: { enabled: false },
    xaxis: { categories, ...AXIS },
    yaxis: [
      {
        ...AXIS,
        max: 100,
        labels: { ...AXIS.labels, formatter: (v) => `${v}%` },
        title: { text: 'Repeat Rate %', style: { fontSize: '11px', color: '#94a3b8' } },
      },
      {
        opposite: true,
        ...AXIS,
        labels: { ...AXIS.labels, formatter: (v) => fmt.number(v, true) },
      },
      { show: false },
    ],
    plotOptions: { bar: { columnWidth: '55%', borderRadius: 4 } },
    tooltip: {
      ...TOOLTIP,
      y: [
        { formatter: (v) => fmt.pct(v) },
        { formatter: (v) => fmt.number(v) + ' customers' },
        { formatter: (v) => fmt.number(v) + ' customers' },
      ],
    },
    grid: GRID,
    legend: { position: 'top', horizontalAlign: 'right', fontSize: '12px', fontFamily: 'Inter' },
  }

  return (
    <Chart
      type="line"
      height={280}
      options={options}
      series={[
        { name: 'Repeat Rate', type: 'line', data: rateData },
        { name: 'New',         type: 'bar',  data: newData },
        { name: 'Returning',   type: 'bar',  data: retData },
      ]}
    />
  )
}
