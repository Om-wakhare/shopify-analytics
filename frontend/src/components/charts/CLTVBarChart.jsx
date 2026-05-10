import Chart from 'react-apexcharts'
import { fmt } from '../../utils/formatters.js'
import { BASE, TOOLTIP, GRID, AXIS } from './chartDefaults.js'

export default function CLTVBarChart({ data = [] }) {
  const items = data.slice(0, 12)
  const labels = items.map((_, i) => `#${i + 1}`)
  const hist   = items.map((d) => +parseFloat(d.historical_cltv_usd || 0).toFixed(2))
  const proj   = items.map((d) => +parseFloat(d.projected_12m_cltv_usd || 0).toFixed(2))

  const options = {
    chart: { ...BASE, type: 'bar', id: 'cltv' },
    colors: ['#7c3aed', '#06b6d4'],
    plotOptions: { bar: { borderRadius: 5, columnWidth: '60%', grouped: true } },
    dataLabels: { enabled: false },
    xaxis: { categories: labels, ...AXIS },
    yaxis: { ...AXIS, labels: { ...AXIS.labels, formatter: (v) => fmt.currency(v, true) } },
    tooltip: { ...TOOLTIP, y: { formatter: (v) => fmt.currency(v) } },
    grid: GRID,
    legend: { position: 'top', horizontalAlign: 'right', fontSize: '12px', fontFamily: 'Inter' },
  }

  return (
    <Chart
      type="bar"
      height={280}
      options={options}
      series={[
        { name: 'Historical CLTV', data: hist },
        { name: 'Projected 12M',   data: proj },
      ]}
    />
  )
}
