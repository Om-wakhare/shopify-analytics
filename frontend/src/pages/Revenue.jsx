import { useState } from 'react'
import Layout from '../components/layout/Layout.jsx'
import { ChartSkeleton } from '../components/ui/Loader.jsx'
import RevenueAreaChart  from '../components/charts/RevenueAreaChart.jsx'
import AOVLineChart      from '../components/charts/AOVLineChart.jsx'
import { useMonthlyRevenue, useAOVTrend } from '../hooks/useKPI.js'
import { fmt } from '../utils/formatters.js'
import clsx from 'clsx'

const PERIODS = [
  { label: '3M',  value: 3 },
  { label: '6M',  value: 6 },
  { label: '12M', value: 12 },
]

function PeriodToggle({ value, onChange }) {
  return (
    <div className="flex bg-slate-100 rounded-xl p-0.5">
      {PERIODS.map((p) => (
        <button
          key={p.value}
          onClick={() => onChange(p.value)}
          className={clsx(
            'px-3 py-1 rounded-lg text-xs font-medium transition-all',
            value === p.value ? 'bg-white text-brand-700 shadow-sm' : 'text-slate-500 hover:text-slate-700',
          )}
        >
          {p.label}
        </button>
      ))}
    </div>
  )
}

export default function Revenue() {
  const [months, setMonths] = useState(12)
  const revenue = useMonthlyRevenue(months + 1)
  const aov     = useAOVTrend('month')
  const data    = revenue.data || []

  const totRev  = data.reduce((s, d) => s + (d.revenue_usd || 0), 0)
  const totOrd  = data.reduce((s, d) => s + (d.order_count || 0), 0)
  const avgAOV  = totOrd ? totRev / totOrd : 0
  const newCust = data.reduce((s, d) => s + (d.new_customers || 0), 0)
  const retCust = data.reduce((s, d) => s + (d.returning_customers || 0), 0)

  return (
    <Layout title="Revenue" subtitle="Detailed revenue analytics and trends">
      {/* Summary strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Revenue',   value: fmt.currency(totRev, true) },
          { label: 'Total Orders',    value: fmt.number(totOrd, true) },
          { label: 'Average AOV',     value: fmt.currency(avgAOV) },
          { label: 'New : Returning', value: `${fmt.number(newCust, true)} : ${fmt.number(retCust, true)}` },
        ].map((s) => (
          <div key={s.label} className="card">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{s.label}</p>
            <p className="text-xl font-bold text-slate-800 mt-1.5">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Revenue chart */}
      <div className="card mb-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="section-title">Revenue Breakdown</p>
            <p className="section-sub">New vs returning customer revenue contribution</p>
          </div>
          <PeriodToggle value={months} onChange={setMonths} />
        </div>
        {revenue.isLoading ? <ChartSkeleton height={320} /> : <RevenueAreaChart data={data} />}
      </div>

      {/* AOV */}
      <div className="card mb-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="section-title">AOV & Order Volume</p>
            <p className="section-sub">Average order value vs total orders per month</p>
          </div>
        </div>
        {aov.isLoading ? <ChartSkeleton height={300} /> : <AOVLineChart data={aov.data} />}
      </div>

      {/* Monthly table */}
      <div className="card">
        <p className="section-title mb-4">Monthly Breakdown</p>
        <div className="overflow-x-auto rounded-xl" style={{ border: '1px solid #f1f5f9' }}>
          <table className="w-full text-sm data-table">
            <thead>
              <tr>
                {['Month','Revenue','Orders','AOV','New Customers','Returning','Rev/Customer'].map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...data].reverse().map((row, i) => (
                <tr key={i}>
                  <td className="font-semibold text-slate-800">{fmt.monthFull(row.month)}</td>
                  <td className="font-bold text-brand-600">{fmt.currency(row.revenue_usd)}</td>
                  <td>{fmt.number(row.order_count)}</td>
                  <td>{fmt.currency(row.aov_usd)}</td>
                  <td className="text-sky-600 font-medium">{fmt.number(row.new_customers)}</td>
                  <td className="text-brand-600 font-medium">{fmt.number(row.returning_customers)}</td>
                  <td>
                    {fmt.currency(row.unique_customers ? row.revenue_usd / row.unique_customers : 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  )
}
