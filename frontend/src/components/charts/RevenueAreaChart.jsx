import Chart from 'react-apexcharts'
import { fmt } from '../../utils/formatters.js'
import { BASE, TOOLTIP, GRID, AXIS } from './chartDefaults.js'

export default function RevenueAreaChart({ data = [] }) {
  const categories = data.map((d) => fmt.month(d.month))
  const newSeries  = data.map((d) => +parseFloat(d.new_customers * parseFloat(d.aov_usd || 0)).toFixed(2))
  const retSeries  = data.map((d) => +parseFloat(d.returning_customers * parseFloat(d.aov_usd || 0)).toFixed(2))

  const options = {
    chart: { ...BASE, type: 'area', stacked: true, id: 'revenue', background: 'transparent' },
    colors: ['#7c3aed', '#06b6d4'],
    fill: {
      type: 'gradient',
      gradient: {
        opacityFrom: 0.6,
        opacityTo:   0.02,
        shadeIntensity: 0.8,
        stops: [0, 90, 100],
      },
    },
    stroke: { curve: 'smooth', width: 2.5 },
    dataLabels: { enabled: false },
    xaxis: { categories, ...AXIS, tooltip: { enabled: false } },
    yaxis: {
      ...AXIS,
      labels: { ...AXIS.labels, formatter: (v) => fmt.currency(v, true) },
    },
    tooltip: {
      ...TOOLTIP,
      y: { formatter: (v) => fmt.currency(v) },
    },
    grid: GRID,
    legend: {
      position: 'top', horizontalAlign: 'right',
      fontSize: '12px', fontFamily: 'Inter',
      markers: { radius: 6 },
    },
  }

  return (
    <Chart
      type="area" height={300}
      options={options}
      series={[
        { name: 'Returning', data: retSeries },
        { name: 'New',       data: newSeries },
      ]}
    />
  )
}
