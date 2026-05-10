import { useEffect, useState } from 'react'
import { X, ShoppingBag, TrendingUp, Clock, Calendar, Mail } from 'lucide-react'
import { fmt } from '../../utils/formatters.js'
import { useStore } from '../../context/StoreContext.jsx'
import clsx from 'clsx'

async function fetchCustomerOrders(shop, customerId, apiKey = 'dev-key') {
  const res = await fetch(
    `/api/kpi/${shop}/cltv?limit=500`,
    { headers: { 'X-API-Key': apiKey } }
  )
  return res.ok ? res.json() : []
}

function StatPill({ icon: Icon, label, value, color = 'brand' }) {
  const bg = { brand: 'bg-brand-50 text-brand-700', emerald: 'bg-emerald-50 text-emerald-700',
                amber: 'bg-amber-50 text-amber-700', sky: 'bg-sky-50 text-sky-700' }
  return (
    <div className={clsx('flex items-center gap-2 px-3 py-2 rounded-xl', bg[color])}>
      <Icon size={14} />
      <div>
        <p className="text-[10px] font-medium uppercase tracking-wide opacity-70">{label}</p>
        <p className="text-sm font-bold leading-none mt-0.5">{value}</p>
      </div>
    </div>
  )
}

export default function CustomerDrawer({ customer, onClose }) {
  const { store } = useStore()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!customer) { setOrders([]); return }
    setLoading(true)
    // In a real app, fetch this customer's orders from a dedicated endpoint
    // For now show the customer details we already have
    setLoading(false)
  }, [customer])

  if (!customer) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-2xl z-50 flex flex-col animate-slide-up"
           style={{ animation: 'slideInRight .3s ease-out' }}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <p className="font-semibold text-slate-800">Customer Profile</p>
            <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1">
              <Mail size={11} />
              {customer.email || 'No email'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-xl flex items-center justify-center text-slate-400 hover:bg-slate-100 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Stats */}
        <div className="px-6 py-4 border-b border-slate-100">
          <div className="grid grid-cols-2 gap-2 mb-3">
            <StatPill icon={TrendingUp} label="Historical CLTV" value={fmt.currency(customer.historical_cltv_usd)} color="brand" />
            <StatPill icon={TrendingUp} label="Projected 12M"   value={fmt.currency(customer.projected_12m_cltv_usd)} color="emerald" />
            <StatPill icon={ShoppingBag} label="Total Orders"   value={fmt.number(customer.total_orders)} color="sky" />
            <StatPill icon={Clock} label="Avg TBO"              value={fmt.days(customer.avg_days_between_orders)} color="amber" />
          </div>

          {/* CLTV progress bar */}
          <div className="mt-3">
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>AOV</span>
              <span>{fmt.currency(customer.aov_usd)}</span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full">
              <div
                className="h-full bg-brand-500 rounded-full transition-all duration-700"
                style={{ width: `${Math.min(100, (parseFloat(customer.aov_usd || 0) / 200) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="px-6 py-4 flex-1 overflow-y-auto">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Activity</p>

          <div className="space-y-3">
            {/* First order */}
            {customer.first_order_at && (
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0 mt-0.5">
                  <ShoppingBag size={13} className="text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-700">First Purchase</p>
                  <p className="text-xs text-slate-400">{fmt.monthFull(customer.first_order_at)}</p>
                </div>
              </div>
            )}

            {/* Last order */}
            {customer.last_order_at && (
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-brand-50 flex items-center justify-center shrink-0 mt-0.5">
                  <Calendar size={13} className="text-brand-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-700">Last Purchase</p>
                  <p className="text-xs text-slate-400">{fmt.monthFull(customer.last_order_at)}</p>
                  <p className="text-xs text-slate-300">{customer.days_since_last_order} days ago</p>
                </div>
              </div>
            )}

            {/* Cohort */}
            {customer.cohort_month && (
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-sky-50 flex items-center justify-center shrink-0 mt-0.5">
                  <TrendingUp size={13} className="text-sky-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-700">Cohort</p>
                  <p className="text-xs text-slate-400">{fmt.monthFull(customer.cohort_month)}</p>
                </div>
              </div>
            )}
          </div>

          {/* Summary card */}
          <div className="mt-6 p-4 bg-slate-50 rounded-2xl border border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Summary</p>
            <div className="space-y-2 text-sm">
              {[
                { label: 'Total Orders',     value: fmt.number(customer.total_orders) },
                { label: 'Total Spent',      value: fmt.currency(customer.historical_cltv_usd) },
                { label: 'Avg Order Value',  value: fmt.currency(customer.aov_usd) },
                { label: 'Purchase Cadence', value: fmt.days(customer.avg_days_between_orders) },
                { label: 'Days Inactive',    value: `${customer.days_since_last_order ?? '—'}d` },
              ].map((row) => (
                <div key={row.label} className="flex justify-between">
                  <span className="text-slate-500">{row.label}</span>
                  <span className="font-semibold text-slate-800">{row.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100">
          <a
            href={`https://${store.domain}/admin/customers`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary w-full justify-center text-sm"
          >
            View in Shopify Admin
          </a>
        </div>
      </div>

      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>
    </>
  )
}
