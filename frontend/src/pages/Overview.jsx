import { DollarSign, ShoppingCart, Users, RefreshCw, TrendingUp, Clock } from 'lucide-react'
import Layout from '../components/layout/Layout.jsx'
import KPICard from '../components/ui/KPICard.jsx'
import { ChartSkeleton } from '../components/ui/Loader.jsx'
import { ErrorBoundary } from '../components/ui/ErrorBoundary.jsx'
import RevenueAreaChart from '../components/charts/RevenueAreaChart.jsx'
import ChurnDonutChart  from '../components/charts/ChurnDonutChart.jsx'
import AOVLineChart     from '../components/charts/AOVLineChart.jsx'
import RepeatRateChart  from '../components/charts/RepeatRateChart.jsx'
import { useSummary, useMonthlyRevenue, useAOVTrend, useRepeatRate, useChurnSummary, useAvgCLTV } from '../hooks/useKPI.js'
import { fmt } from '../utils/formatters.js'

function ChartCard({ title, subtitle, children, action }) {
  return (
    <div className="card animate-fade-in">
      <div className="flex items-start justify-between mb-5">
        <div>
          <p className="section-title">{title}</p>
          {subtitle && <p className="section-sub">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </div>
  )
}

export default function Overview() {
  const summary = useSummary()
  const revenue = useMonthlyRevenue(13)
  const aov     = useAOVTrend('month')
  const repeat  = useRepeatRate(13)
  const churn   = useChurnSummary()
  const cltv    = useAvgCLTV()

  const s = summary.data
  const c = cltv.data

  return (
    <Layout title="Overview" subtitle="Store-wide performance at a glance">

      {/* ── Tier 1 KPIs ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-4">
        <KPICard
          label="Total Revenue" icon={DollarSign} color="brand"
          value={s ? fmt.currency(s.total_revenue_usd, true) : '—'}
          subValue={s ? `${fmt.number(s.total_orders, true)} paid orders` : null}
          trend={8.4} trendLabel="+8.4%" loading={summary.isLoading}
        />
        <KPICard
          label="Avg Order Value" icon={ShoppingCart} color="sky"
          value={s ? fmt.currency(s.aov_usd) : '—'}
          subValue="Per paid order"
          trend={3.1} trendLabel="+3.1%" loading={summary.isLoading}
        />
        <KPICard
          label="Repeat Order Rate" icon={RefreshCw} color="emerald"
          value={s ? fmt.pct(s.repeat_order_rate_pct) : '—'}
          subValue={s ? `${fmt.number(s.repeat_customers, true)} repeat buyers` : null}
          trend={2.8} trendLabel="+2.8%" loading={summary.isLoading}
        />
        <KPICard
          label="Avg CLTV" icon={Users} color="amber"
          value={c ? fmt.currency(c.avg_historical_cltv) : '—'}
          subValue={c ? `${fmt.currency(c.avg_projected_12m_cltv)} projected 12M` : null}
          trend={5.2} trendLabel="+5.2%" loading={cltv.isLoading}
        />
      </div>

      {/* ── Tier 2 KPIs ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <KPICard
          label="Avg Time Between Orders" icon={Clock} color="rose"
          value={c ? fmt.days(c.avg_tbo_days) : '—'}
          subValue="Repeat customers" loading={cltv.isLoading}
        />
        <KPICard
          label="Total Customers" icon={Users} color="brand"
          value={s ? fmt.number(s.total_customers, true) : '—'}
          subValue={s ? `${fmt.number(s.repeat_customers, true)} repeat` : null}
          loading={summary.isLoading}
        />
        <KPICard
          label="Total Orders" icon={ShoppingCart} color="sky"
          value={s ? fmt.number(s.total_orders, true) : '—'}
          subValue="All time, paid" loading={summary.isLoading}
        />
        <KPICard
          label="Proj. 12M CLTV" icon={TrendingUp} color="emerald"
          value={c ? fmt.currency(c.avg_projected_12m_cltv) : '—'}
          subValue="Per customer average" loading={cltv.isLoading}
        />
      </div>

      {/* ── Revenue + Churn ──────────────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-4">
        <div className="xl:col-span-2">
          {revenue.isLoading
            ? <ChartSkeleton height={370} />
            : <ChartCard title="Revenue Over Time" subtitle="New vs returning customer revenue split">
                <ErrorBoundary><RevenueAreaChart data={revenue.data} /></ErrorBoundary>
              </ChartCard>
          }
        </div>
        <div>
          {churn.isLoading
            ? <ChartSkeleton height={370} />
            : <ChartCard title="Churn Risk Tiers" subtitle="Current customer risk breakdown">
                <ErrorBoundary><ChurnDonutChart data={churn.data} /></ErrorBoundary>
              </ChartCard>
          }
        </div>
      </div>

      {/* ── AOV + Repeat ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div>
          {aov.isLoading
            ? <ChartSkeleton height={330} />
            : <ChartCard title="AOV Trend" subtitle="Average order value and order volume">
                <ErrorBoundary><AOVLineChart data={aov.data} /></ErrorBoundary>
              </ChartCard>
          }
        </div>
        <div>
          {repeat.isLoading
            ? <ChartSkeleton height={330} />
            : <ChartCard title="Repeat Order Rate" subtitle="Monthly new vs returning customer breakdown">
                <ErrorBoundary><RepeatRateChart data={repeat.data} /></ErrorBoundary>
              </ChartCard>
          }
        </div>
      </div>

    </Layout>
  )
}
