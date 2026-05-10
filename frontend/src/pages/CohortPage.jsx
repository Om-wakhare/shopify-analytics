import Layout from '../components/layout/Layout.jsx'
import { ChartSkeleton } from '../components/ui/Loader.jsx'
import CohortHeatmap from '../components/charts/CohortHeatmap.jsx'
import { useCohortRetention } from '../hooks/useKPI.js'
import { fmt } from '../utils/formatters.js'

function InsightCard({ title, value, description, color = 'brand' }) {
  const bg = { brand: 'bg-brand-50 border-brand-100', emerald: 'bg-emerald-50 border-emerald-100', amber: 'bg-amber-50 border-amber-100' }
  const text = { brand: 'text-brand-700', emerald: 'text-emerald-700', amber: 'text-amber-700' }
  return (
    <div className={`rounded-2xl border p-4 ${bg[color]}`}>
      <p className={`text-xs font-semibold uppercase tracking-wide ${text[color]}`}>{title}</p>
      <p className={`text-2xl font-bold mt-1 ${text[color]}`}>{value}</p>
      <p className="text-xs text-slate-500 mt-1">{description}</p>
    </div>
  )
}

export default function CohortPage() {
  const cohorts = useCohortRetention()
  const data    = cohorts.data || []

  // Derive insights
  const m1Rows  = data.filter((d) => +d.month_offset === 1)
  const m3Rows  = data.filter((d) => +d.month_offset === 3)
  const avgM1   = m1Rows.length ? m1Rows.reduce((s, d) => s + +d.retention_rate_pct, 0) / m1Rows.length : null
  const avgM3   = m3Rows.length ? m3Rows.reduce((s, d) => s + +d.retention_rate_pct, 0) / m3Rows.length : null
  const latest  = data.filter((d) => +d.month_offset === 0).at(-1)

  return (
    <Layout title="Cohort Retention" subtitle="Monthly cohort retention heatmap">
      {/* Insights strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <InsightCard
          title="Latest Cohort Size"
          value={latest ? fmt.number(latest.cohort_size) : '—'}
          description="Customers acquired in most recent month"
          color="brand"
        />
        <InsightCard
          title="Avg M1 Retention"
          value={avgM1 != null ? fmt.pct(avgM1) : '—'}
          description="% of cohort returning in month 2"
          color="emerald"
        />
        <InsightCard
          title="Avg M3 Retention"
          value={avgM3 != null ? fmt.pct(avgM3) : '—'}
          description="% of cohort returning in month 4"
          color="amber"
        />
        <InsightCard
          title="Total Cohorts"
          value={fmt.number(new Set(data.map((d) => d.cohort_month)).size)}
          description="Months of cohort data available"
          color="brand"
        />
      </div>

      {/* Heatmap */}
      <div className="card mb-4">
        <div className="mb-4">
          <p className="section-title">Retention Heatmap</p>
          <p className="section-sub">
            Each row = an acquisition cohort. Each column = months since first purchase.
            Darker = higher retention. Hover a cell for details.
          </p>
        </div>
        {cohorts.isLoading ? (
          <ChartSkeleton height={380} />
        ) : (
          <CohortHeatmap data={data} />
        )}
      </div>

      {/* Per-cohort table */}
      <div className="card">
        <p className="section-title mb-4">Cohort Details — Month 0 → 6</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Cohort</th>
                <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Size</th>
                {[0,1,2,3,4,5,6].map((m) => (
                  <th key={m} className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">M{m}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...new Set(data.map((d) => d.cohort_month))].sort().map((cohort) => {
                const rows = data.filter((d) => d.cohort_month === cohort)
                const byOffset = Object.fromEntries(rows.map((r) => [r.month_offset, r]))
                const size = byOffset[0]?.cohort_size || '—'
                return (
                  <tr key={cohort} className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-3 font-medium text-slate-700">{fmt.monthFull(cohort)}</td>
                    <td className="py-3 px-3 text-slate-600">{fmt.number(size)}</td>
                    {[0,1,2,3,4,5,6].map((m) => {
                      const r = byOffset[m]
                      const pct = r ? +r.retention_rate_pct : null
                      return (
                        <td key={m} className="py-3 px-3">
                          {pct != null ? (
                            <span
                              className="inline-flex items-center justify-center w-14 py-0.5 rounded-lg text-xs font-semibold"
                              style={{
                                background: `rgba(109, 40, 217, ${0.08 + (pct / 100) * 0.55})`,
                                color: pct > 50 ? '#4c1d95' : '#7c3aed',
                              }}
                            >
                              {fmt.pct(pct, 0)}
                            </span>
                          ) : (
                            <span className="text-slate-200 text-xs">—</span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  )
}
