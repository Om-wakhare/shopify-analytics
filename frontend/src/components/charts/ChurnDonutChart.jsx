import Chart from 'react-apexcharts'
import { fmt } from '../../utils/formatters.js'
import { BASE } from './chartDefaults.js'

const TIER_META = {
  healthy:        { label: 'Healthy',        color: '#10b981' },
  low_risk:       { label: 'Low Risk',       color: '#f59e0b' },
  medium_risk:    { label: 'Medium Risk',    color: '#f97316' },
  high_risk:      { label: 'High Risk',      color: '#f43f5e' },
  one_time_buyer: { label: 'One-time Buyer', color: '#94a3b8' },
}

export default function ChurnDonutChart({ data = [] }) {
  const ordered = ['healthy','low_risk','medium_risk','high_risk','one_time_buyer']
  const rows    = ordered.map(k => data.find(d => d.churn_risk_tier === k)).filter(Boolean)

  const labels  = rows.map(r => TIER_META[r.churn_risk_tier]?.label || r.churn_risk_tier)
  const series  = rows.map(r => r.customer_count || 0)
  const colors  = rows.map(r => TIER_META[r.churn_risk_tier]?.color || '#94a3b8')
  const atRisk  = rows.filter(r => r.churn_risk_tier !== 'healthy').reduce((a, r) => a + r.customer_count, 0)

  const options = {
    chart: { ...BASE, type: 'donut', background: 'transparent' },
    colors,
    labels,
    dataLabels: { enabled: false },
    legend: {
      position: 'bottom', fontSize: '12px', fontFamily: 'Inter',
      markers: { radius: 4, width: 8, height: 8 },
      itemMargin: { horizontal: 8, vertical: 4 },
    },
    plotOptions: {
      pie: {
        donut: {
          size: '72%',
          labels: {
            show:  true,
            name:  { show: true, fontSize: '12px', fontFamily: 'Inter', color: '#64748b', offsetY: 4 },
            value: { show: true, fontSize: '24px', fontFamily: 'Inter', fontWeight: 800, color: '#0f172a',
                     formatter: v => fmt.number(+v) },
            total: {
              show:      true,
              label:     'At Risk',
              fontSize:  '11px',
              fontWeight: 600,
              color:     '#94a3b8',
              formatter: () => fmt.number(atRisk),
            },
          },
        },
      },
    },
    tooltip: {
      theme: 'light',
      style: { fontFamily: 'Inter', fontSize: '12px' },
      y: { formatter: v => `${fmt.number(v)} customers` },
    },
    stroke: { width: 3, colors: ['#f4f6fb'] },
  }

  return <Chart type="donut" height={320} options={options} series={series} />
}
