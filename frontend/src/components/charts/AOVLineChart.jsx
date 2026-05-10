import Chart from 'react-apexcharts'
import { fmt } from '../../utils/formatters.js'
import { BASE, TOOLTIP, GRID, AXIS } from './chartDefaults.js'

export default function AOVLineChart({ data = [] }) {
  const categories = data.map((d) => fmt.month(d.period || d.month))
  const aovData    = data.map((d) => +parseFloat(d.aov_usd || 0).toFixed(2))
  const ordData    = data.map((d) => d.order_count || 0)

  const options = {
    chart: { ...BASE, type: 'line', id: 'aov' },
    colors: ['#7c3aed', '#06b6d4'],
    stroke: { curve: 'smooth', width: [3, 2], dashArray: [0, 4] },
    dataLabels: { enabled: false },
    xaxis: { categories, ...AXIS },
    yaxis: [
      {
        ...AXIS,
        title: { text: 'AOV (USD)', style: { fontSize: '11px', color: '#94a3b8' } },
        labels: { ...AXIS.labels, formatter: (v) => fmt.currency(v) },
      },
      {
        opposite: true,
        ...AXIS,
        title: { text: 'Orders', style: { fontSize: '11px', color: '#94a3b8' } },
        labels: { ...AXIS.labels, formatter: (v) => fmt.number(v, true) },
      },
    ],
    tooltip: { ...TOOLTIP, y: [{ formatter: (v) => fmt.currency(v) }, { formatter: (v) => fmt.number(v) + ' orders' }] },
    grid: GRID,
    markers: { size: [0, 0], hover: { size: 5 } },
    legend: { position: 'top', horizontalAlign: 'right', fontSize: '12px', fontFamily: 'Inter' },
  }

  return (
    <Chart
      type="line"
      height={280}
      options={options}
      series={[
        { name: 'AOV',    data: aovData },
        { name: 'Orders', data: ordData },
      ]}
    />
  )
}
