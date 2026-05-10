import Chart from 'react-apexcharts'
import { fmt } from '../../utils/formatters.js'
import { BASE, TOOLTIP, GRID, AXIS } from './chartDefaults.js'

export default function TBOHistogram({ data = [] }) {
  const categories = data.map((d) => d.bucket)
  const counts     = data.map((d) => d.customer_count)

  const options = {
    chart: { ...BASE, type: 'bar', id: 'tbo' },
    colors: ['#7c3aed'],
    plotOptions: {
      bar: {
        borderRadius: 6,
        columnWidth: '65%',
        distributed: true,
        dataLabels: { position: 'top' },
      },
    },
    dataLabels: {
      enabled: true,
      formatter: (v) => fmt.number(v, true),
      offsetY: -22,
      style: { fontSize: '11px', fontFamily: 'Inter', colors: ['#64748b'], fontWeight: 600 },
    },
    fill: {
      type: 'gradient',
      gradient: { shade: 'light', type: 'vertical', gradientToColors: ['#a78bfa'], opacityFrom: 1, opacityTo: 0.7 },
    },
    xaxis: { categories, ...AXIS },
    yaxis: {
      ...AXIS,
      labels: { ...AXIS.labels, formatter: (v) => fmt.number(v, true) },
    },
    tooltip: { ...TOOLTIP, y: { formatter: (v) => `${fmt.number(v)} customers` } },
    grid: GRID,
    legend: { show: false },
    colors: data.map((_, i) => {
      const opacity = 0.55 + (i / data.length) * 0.45
      return `rgba(124, 58, 237, ${opacity})`
    }),
  }

  return <Chart type="bar" height={280} options={options} series={[{ name: 'Customers', data: counts }]} />
}
