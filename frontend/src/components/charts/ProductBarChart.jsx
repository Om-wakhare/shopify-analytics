import Chart from 'react-apexcharts'
import { fmt } from '../../utils/formatters.js'
import { BASE, TOOLTIP, GRID, AXIS } from './chartDefaults.js'

export default function ProductBarChart({ data = [] }) {
  const items = [...data].sort((a, b) => b.revenue_usd - a.revenue_usd).slice(0, 10)
  const labels  = items.map((d) => d.product_title?.length > 20 ? d.product_title.slice(0, 18) + '…' : d.product_title)
  const revenue = items.map((d) => +parseFloat(d.revenue_usd || 0).toFixed(2))
  const orders  = items.map((d) => d.order_count || 0)

  const options = {
    chart: { ...BASE, type: 'bar', id: 'products' },
    colors: ['#7c3aed'],
    plotOptions: {
      bar: {
        horizontal:  true,
        borderRadius: 6,
        barHeight:   '65%',
        dataLabels:  { position: 'top' },
      },
    },
    dataLabels: {
      enabled: true,
      formatter: (v) => fmt.currency(v, true),
      offsetX: 6,
      style: { fontSize: '10px', fontFamily: 'Inter', colors: ['#64748b'], fontWeight: 600 },
    },
    fill: {
      type: 'gradient',
      gradient: { shade: 'light', type: 'horizontal', gradientToColors: ['#c4b5fd'], opacityFrom: 1, opacityTo: 0.7 },
    },
    xaxis: {
      categories: labels,
      ...AXIS,
      labels: { ...AXIS.labels, formatter: (v) => fmt.currency(v, true) },
    },
    yaxis: { ...AXIS },
    tooltip: { ...TOOLTIP, y: { formatter: (v) => fmt.currency(v) } },
    grid: { ...GRID, yaxis: { lines: { show: false } }, xaxis: { lines: { show: true } } },
    legend: { show: false },
  }

  return <Chart type="bar" height={360} options={options} series={[{ name: 'Revenue', data: revenue }]} />
}
