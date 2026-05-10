import Layout from '../components/layout/Layout.jsx'
import { ChartSkeleton } from '../components/ui/Loader.jsx'
import RepeatRateChart from '../components/charts/RepeatRateChart.jsx'
import AOVLineChart    from '../components/charts/AOVLineChart.jsx'
import { useRepeatRate, useSummary } from '../hooks/useKPI.js'
import { fmt } from '../utils/formatters.js'

export default function RepeatPage() {
  const repeat  = useRepeatRate(13)
  const summary = useSummary()
  const data    = repeat.data || []
  const s       = summary.data

  const avgRate = data.length
    ? data.reduce((sum, d) => sum + +d.repeat_order_rate_pct, 0) / data.length
    : null

  return (
    <Layout title="Repeat Rate" subtitle="Repeat purchase behavior and trends">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Overall Repeat Rate', value: s ? fmt.pct(s.repeat_order_rate_pct) : '—' },
          { label: 'Avg Monthly Rate',    value: avgRate != null ? fmt.pct(avgRate) : '—' },
          { label: 'Repeat Customers',    value: s ? fmt.number(s.repeat_customers, true) : '—' },
          { label: 'Total Customers',     value: s ? fmt.number(s.total_customers, true) : '—' },
        ].map((s) => (
          <div key={s.label} className="card">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{s.label}</p>
            <p className="text-xl font-bold text-slate-800 mt-1.5">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="card mb-4">
        <p className="section-title">Repeat Rate Over Time</p>
        <p className="section-sub mb-4">Monthly new vs returning customer split and repeat rate %</p>
        {repeat.isLoading ? <ChartSkeleton height={320} /> : <RepeatRateChart data={data} />}
      </div>

      <div className="card">
        <p className="section-title mb-4">Monthly Repeat Rate Data</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                {['Month','New Customers','Returning','Total','Repeat Rate'].map((h) => (
                  <th key={h} className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...data].reverse().map((row, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/60">
                  <td className="py-3 px-3 font-medium text-slate-700">{fmt.monthFull(row.month)}</td>
                  <td className="py-3 px-3 text-sky-600 font-medium">{fmt.number(row.new_customers)}</td>
                  <td className="py-3 px-3 text-brand-600 font-medium">{fmt.number(row.repeat_customers)}</td>
                  <td className="py-3 px-3 text-slate-600">{fmt.number((row.new_customers || 0) + (row.repeat_customers || 0))}</td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-slate-100 rounded-full max-w-[80px]">
                        <div className="h-full bg-brand-500 rounded-full" style={{ width: `${row.repeat_order_rate_pct}%` }} />
                      </div>
                      <span className="text-xs font-semibold text-brand-700">{fmt.pct(row.repeat_order_rate_pct)}</span>
                    </div>
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
