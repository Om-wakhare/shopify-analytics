import { useState } from 'react'
import Layout from '../components/layout/Layout.jsx'
import { ChartSkeleton, TableSkeleton } from '../components/ui/Loader.jsx'
import { ErrorBoundary } from '../components/ui/ErrorBoundary.jsx'
import ExportButton from '../components/ui/ExportButton.jsx'
import ChurnDonutChart from '../components/charts/ChurnDonutChart.jsx'
import { useChurnSummary, useChurnSignals } from '../hooks/useKPI.js'
import { fmt } from '../utils/formatters.js'
import clsx from 'clsx'

const TIER_META = {
  high_risk:       { label: 'High Risk',      bg: 'bg-rose-50   text-rose-700   border-rose-100',   dot: 'bg-rose-500'   },
  medium_risk:     { label: 'Medium Risk',    bg: 'bg-orange-50 text-orange-700 border-orange-100', dot: 'bg-orange-500' },
  low_risk:        { label: 'Low Risk',       bg: 'bg-amber-50  text-amber-700  border-amber-100',  dot: 'bg-amber-500'  },
  one_time_buyer:  { label: 'One-time Buyer', bg: 'bg-slate-50  text-slate-600  border-slate-200',  dot: 'bg-slate-400'  },
  healthy:         { label: 'Healthy',        bg: 'bg-emerald-50 text-emerald-700 border-emerald-100', dot: 'bg-emerald-500' },
}

const ALL_TIERS = ['', 'high_risk', 'medium_risk', 'low_risk', 'one_time_buyer']

const CHURN_COLUMNS = [
  { label: 'Customer',           accessor: (r) => r.email || r.customer_id },
  { label: 'Risk Tier',          accessor: (r) => TIER_META[r.churn_risk_tier]?.label || r.churn_risk_tier },
  { label: 'Historical CLTV',    accessor: (r) => r.historical_cltv_usd },
  { label: 'Total Orders',       accessor: (r) => r.total_orders },
  { label: 'Days Since Last',    accessor: (r) => r.days_since_last_order },
  { label: 'Avg TBO',            accessor: (r) => r.avg_days_between_orders },
  { label: 'Last Order',         accessor: (r) => r.last_order_at },
]

export default function ChurnPage() {
  const [tier, setTier] = useState('')
  const summary = useChurnSummary()
  const signals = useChurnSignals(tier)
  const s = summary.data || []

  const totalAtRisk   = s.filter((r) => r.churn_risk_tier !== 'healthy').reduce((a, r) => a + r.customer_count, 0)
  const revenueAtRisk = s.filter((r) => r.churn_risk_tier !== 'healthy').reduce((a, r) => a + +r.revenue_at_risk_usd, 0)

  return (
    <Layout title="Churn Analysis" subtitle="At-risk customers and revenue at risk">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Total At-Risk</p>
          <p className="text-2xl font-bold text-rose-600 mt-2">{fmt.number(totalAtRisk)}</p>
          <p className="text-xs text-slate-400 mt-1">Across all risk tiers</p>
        </div>
        <div className="card">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Revenue At Risk</p>
          <p className="text-2xl font-bold text-orange-600 mt-2">{fmt.currency(revenueAtRisk, true)}</p>
          <p className="text-xs text-slate-400 mt-1">Potential lost revenue</p>
        </div>
        {s.filter((r) => r.churn_risk_tier === 'high_risk' || r.churn_risk_tier === 'medium_risk').map((r) => (
          <div key={r.churn_risk_tier} className={clsx('rounded-2xl border p-4', TIER_META[r.churn_risk_tier]?.bg)}>
            <p className="text-xs font-semibold uppercase tracking-wide">{TIER_META[r.churn_risk_tier]?.label}</p>
            <p className="text-2xl font-bold mt-1">{fmt.number(r.customer_count)}</p>
            <p className="text-xs opacity-70 mt-1">{fmt.currency(r.revenue_at_risk_usd, true)} at risk</p>
          </div>
        ))}
      </div>

      {/* Donut + tier breakdown */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-4">
        <div className="card">
          <p className="section-title mb-1">Risk Distribution</p>
          <p className="section-sub mb-2">Churn tier breakdown</p>
          <ErrorBoundary>
            {summary.isLoading ? <ChartSkeleton height={340} /> : <ChurnDonutChart data={s} />}
          </ErrorBoundary>
        </div>

        <div className="xl:col-span-2 card">
          <p className="section-title mb-4">Tier Breakdown</p>
          <div className="space-y-3">
            {s.map((row) => {
              const meta = TIER_META[row.churn_risk_tier] || {}
              const total = s.reduce((a, r) => a + r.customer_count, 0)
              const pct = total ? (row.customer_count / total) * 100 : 0
              return (
                <div key={row.churn_risk_tier}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className={clsx('w-2 h-2 rounded-full', meta.dot || 'bg-slate-300')} />
                      <span className="text-sm font-medium text-slate-700">{meta.label || row.churn_risk_tier}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-slate-500">{fmt.number(row.customer_count)} customers</span>
                      <span className="font-semibold text-slate-700 w-16 text-right">{fmt.pct(pct, 0)}</span>
                    </div>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700 bg-current"
                         style={{ width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* At-risk customer list */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="section-title">At-Risk Customers</p>
            <p className="section-sub">Ranked by revenue at risk</p>
          </div>
          <div className="flex items-center gap-2">
            <ExportButton data={signals.data} columns={CHURN_COLUMNS} filename="churn_signals.csv" />
            <div className="flex gap-1.5">
              {ALL_TIERS.map((t) => (
                <button
                  key={t || 'all'}
                  onClick={() => setTier(t)}
                  className={clsx(
                    'px-3 py-1.5 rounded-xl text-xs font-medium transition-all',
                    tier === t
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
                  )}
                >
                  {t ? (TIER_META[t]?.label || t) : 'All'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {signals.isLoading ? <TableSkeleton rows={10} /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  {['Customer','Risk Tier','CLTV','Orders','Days Since Last Order','Avg TBO','Last Order'].map((h) => (
                    <th key={h} className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(signals.data || []).map((c, i) => {
                  const meta = TIER_META[c.churn_risk_tier] || {}
                  return (
                    <tr key={c.customer_id} className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors">
                      <td className="py-3 px-3 font-medium text-slate-700 truncate max-w-[160px]">{c.email || `Customer ${i+1}`}</td>
                      <td className="py-3 px-3">
                        <span className={clsx('badge border', meta.bg || 'badge-info')}>{meta.label || c.churn_risk_tier}</span>
                      </td>
                      <td className="py-3 px-3 font-semibold text-brand-600">{fmt.currency(c.historical_cltv_usd)}</td>
                      <td className="py-3 px-3 text-slate-600">{c.total_orders}</td>
                      <td className="py-3 px-3">
                        <span className={clsx('font-semibold', c.days_since_last_order > 90 ? 'text-rose-600' : 'text-amber-600')}>
                          {c.days_since_last_order}d
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-600">{fmt.days(c.avg_days_between_orders)}</td>
                      <td className="py-3 px-3 text-slate-500 text-xs">{fmt.month(c.last_order_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}
