import Layout from '../components/layout/Layout.jsx'
import { ChartSkeleton, TableSkeleton } from '../components/ui/Loader.jsx'
import { ErrorBoundary } from '../components/ui/ErrorBoundary.jsx'
import ExportButton from '../components/ui/ExportButton.jsx'
import CLTVBarChart  from '../components/charts/CLTVBarChart.jsx'
import TBOHistogram  from '../components/charts/TBOHistogram.jsx'
import { useAvgCLTV, useTopCustomers, useTBODistribution } from '../hooks/useKPI.js'
import { fmt } from '../utils/formatters.js'
import { useState } from 'react'
import CustomerDrawer from '../components/ui/CustomerDrawer.jsx'

const CUSTOMER_COLUMNS = [
  { label: 'Email',             accessor: (r) => r.email || `Customer #${r.customer_id?.slice(0,8)}` },
  { label: 'Total Orders',      accessor: (r) => r.total_orders },
  { label: 'Historical CLTV',   accessor: (r) => r.historical_cltv_usd },
  { label: 'Projected 12M',     accessor: (r) => r.projected_12m_cltv_usd },
  { label: 'AOV',               accessor: (r) => r.aov_usd },
  { label: 'Avg TBO (days)',     accessor: (r) => r.avg_days_between_orders },
  { label: 'Days Since Last',   accessor: (r) => r.days_since_last_order },
]

function MetricBox({ label, value, sub }) {
  return (
    <div className="card text-center">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-brand-600 mt-2">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  )
}

export default function CLTVPage() {
  const avg       = useAvgCLTV()
  const customers = useTopCustomers(20)
  const tbo       = useTBODistribution()
  const a         = avg.data
  const [selected, setSelected] = useState(null)

  return (
    <Layout title="CLTV" subtitle="Customer Lifetime Value analysis">
      {/* Summary metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <MetricBox label="Customers"           value={a ? fmt.number(a.customer_count, true) : '—'} />
        <MetricBox label="Avg Historical CLTV" value={a ? fmt.currency(a.avg_historical_cltv) : '—'} sub="All-time per customer" />
        <MetricBox label="Avg Projected 12M"   value={a ? fmt.currency(a.avg_projected_12m_cltv) : '—'} sub="Projected revenue" />
        <MetricBox label="Avg AOV"             value={a ? fmt.currency(a.avg_aov) : '—'} sub="Per order" />
        <MetricBox label="Avg Time Btw Orders" value={a ? fmt.days(a.avg_tbo_days) : '—'} sub="Repeat buyers" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-4">
        <div className="card">
          <p className="section-title">Top 12 Customers — CLTV</p>
          <p className="section-sub mb-4">Historical vs projected 12-month revenue</p>
          <ErrorBoundary>
            {customers.isLoading ? <ChartSkeleton height={300} /> : <CLTVBarChart data={customers.data} />}
          </ErrorBoundary>
        </div>
        <div className="card">
          <p className="section-title">Time Between Orders</p>
          <p className="section-sub mb-4">Distribution of purchase cadence across repeat buyers</p>
          <ErrorBoundary>
            {tbo.isLoading ? <ChartSkeleton height={300} /> : <TBOHistogram data={tbo.data} />}
          </ErrorBoundary>
        </div>
      </div>

      {/* Top customers table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <p className="section-title">Top Customers by CLTV</p>
          <ExportButton
            data={customers.data}
            columns={CUSTOMER_COLUMNS}
            filename="cltv_customers.csv"
          />
        </div>
        {customers.isLoading ? <TableSkeleton rows={10} /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  {['#','Customer','Total Orders','Historical CLTV','Projected 12M','AOV','Avg TBO','Last Order'].map((h) => (
                    <th key={h} className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(customers.data || []).map((c, i) => (
                  <tr
                    key={c.customer_id}
                    onClick={() => setSelected(c)}
                    className="border-b border-slate-50 hover:bg-brand-50/50 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-3 text-slate-400 text-xs font-medium">{i + 1}</td>
                    <td className="py-3 px-3">
                      <span className="font-medium text-brand-600 hover:underline truncate block max-w-[140px]">
                        {c.email || `Customer #${i+1}`}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-600">{c.total_orders}</td>
                    <td className="py-3 px-3 font-semibold text-brand-600">{fmt.currency(c.historical_cltv_usd)}</td>
                    <td className="py-3 px-3 text-emerald-600 font-medium">{fmt.currency(c.projected_12m_cltv_usd)}</td>
                    <td className="py-3 px-3 text-slate-600">{fmt.currency(c.aov_usd)}</td>
                    <td className="py-3 px-3 text-slate-600">{fmt.days(c.avg_days_between_orders)}</td>
                    <td className="py-3 px-3 text-slate-500 text-xs">{c.days_since_last_order}d ago</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Customer Detail Drawer */}
      <CustomerDrawer customer={selected} onClose={() => setSelected(null)} />
    </Layout>
  )
}
