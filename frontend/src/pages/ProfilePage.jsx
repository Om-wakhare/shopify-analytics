import Layout from '../components/layout/Layout.jsx'
import { useShopInfo } from '../hooks/useKPI.js'
import { useAuth } from '../context/AuthContext.jsx'
import { fmt } from '../utils/formatters.js'
import {
  Store, Mail, Globe, Clock, CreditCard, Users,
  ShoppingCart, RefreshCw, AlertTriangle, ExternalLink,
  Crown, Zap, Star,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'

const PLAN_META = {
  starter: { icon: Zap,   color: 'text-sky-600',   bg: 'bg-sky-50',   label: 'Starter',  price: '$29/mo' },
  growth:  { icon: Star,  color: 'text-brand-600', bg: 'bg-brand-50', label: 'Growth',   price: '$79/mo' },
  pro:     { icon: Crown, color: 'text-amber-600', bg: 'bg-amber-50', label: 'Pro',       price: '$199/mo' },
  trial:   { icon: Zap,   color: 'text-emerald-600', bg: 'bg-emerald-50', label: 'Free Trial', price: 'Free' },
}

function InfoRow({ icon: Icon, label, value, highlight }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-50 last:border-0">
      <div className="flex items-center gap-2.5 text-slate-500">
        <Icon size={14} className="shrink-0" />
        <span className="text-sm">{label}</span>
      </div>
      <span className={clsx('text-sm font-medium', highlight ? 'text-brand-600' : 'text-slate-800')}>
        {value || '—'}
      </span>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color = 'brand' }) {
  const colors = {
    brand:   'bg-brand-50 text-brand-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    sky:     'bg-sky-50 text-sky-600',
    amber:   'bg-amber-50 text-amber-600',
  }
  return (
    <div className="card text-center py-5">
      <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-3', colors[color])}>
        <Icon size={18} />
      </div>
      <p className="text-2xl font-bold text-slate-800">{value}</p>
      <p className="text-xs text-slate-400 mt-1">{label}</p>
    </div>
  )
}

export default function ProfilePage() {
  const { data: shop, isLoading } = useShopInfo()
  const { logout }                = useAuth()
  const navigate                  = useNavigate()

  const subStatus  = shop?.subscription_status || 'trial'
  const planKey    = shop?.subscription_plan || 'trial'
  const plan       = PLAN_META[planKey] || PLAN_META.trial
  const PlanIcon   = plan.icon

  const trialDaysLeft = shop?.trial_ends_at
    ? Math.max(0, Math.ceil((new Date(shop.trial_ends_at) - Date.now()) / 86400000))
    : null

  if (isLoading) return (
    <Layout>
      <div className="space-y-4">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="card animate-pulse h-40" />
        ))}
      </div>
    </Layout>
  )

  return (
    <Layout>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-4">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center text-white text-xl font-bold shrink-0"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)' }}
          >
            {(shop?.shop_domain?.[0] || 'S').toUpperCase()}
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">{shop?.shop_name || shop?.shop_domain}</h1>
            <p className="text-sm text-slate-400 mt-0.5">{shop?.shop_domain}</p>
          </div>
        </div>
        {shop?.primary_domain && (
          <a
            href={shop.primary_domain}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost text-xs"
          >
            <ExternalLink size={13} /> Visit Store
          </a>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard icon={Users}        label="Customers Synced"  value={fmt.number(shop?.customers_synced, true)} color="brand" />
        <StatCard icon={ShoppingCart} label="Orders Synced"     value={fmt.number(shop?.orders_synced, true)}    color="sky" />
        <StatCard icon={RefreshCw}    label="Last Sync"         value={shop?.last_sync_at ? fmt.month(shop.last_sync_at) : 'Never'} color="emerald" />
        <StatCard icon={CreditCard}   label="Current Plan"      value={plan.label}                                color="amber" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Store Details */}
        <div className="card">
          <p className="section-title mb-4">Store Details</p>
          <InfoRow icon={Store}  label="Store Name"   value={shop?.shop_name} />
          <InfoRow icon={Globe}  label="Domain"       value={shop?.shop_domain} highlight />
          <InfoRow icon={Mail}   label="Owner Email"  value={shop?.shop_owner_email} />
          <InfoRow icon={Users}  label="Owner Name"   value={shop?.shop_owner_name} />
          <InfoRow icon={CreditCard} label="Shopify Plan" value={shop?.shop_plan} />
          <InfoRow icon={Globe}  label="Currency"     value={shop?.currency} />
          <InfoRow icon={Clock}  label="Timezone"     value={shop?.timezone} />
          <InfoRow icon={RefreshCw} label="Installed" value={shop?.installed_at ? fmt.monthFull(shop.installed_at) : '—'} />
        </div>

        {/* Subscription */}
        <div className="space-y-4">
          <div className="card">
            <p className="section-title mb-4">Subscription</p>

            {/* Plan badge */}
            <div className={clsx('flex items-center gap-3 p-4 rounded-xl mb-4', plan.bg)}>
              <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center', plan.bg)}>
                <PlanIcon size={18} className={plan.color} />
              </div>
              <div className="flex-1">
                <p className={clsx('font-bold', plan.color)}>{plan.label}</p>
                <p className="text-xs text-slate-500">{plan.price}</p>
              </div>
              {subStatus === 'trial' && trialDaysLeft !== null && (
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-1 rounded-lg">
                  {trialDaysLeft}d left
                </span>
              )}
              {subStatus === 'active' && (
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-1 rounded-lg">
                  Active
                </span>
              )}
            </div>

            <InfoRow icon={CreditCard} label="Status"        value={subStatus}                                                      highlight />
            <InfoRow icon={Clock}      label="Trial Ends"    value={shop?.trial_ends_at ? fmt.monthFull(shop.trial_ends_at) : '—'} />
            <InfoRow icon={Clock}      label="Subscribed"    value={shop?.subscribed_at  ? fmt.monthFull(shop.subscribed_at)  : '—'} />

            {subStatus !== 'active' && (
              <button
                onClick={() => navigate('/subscribe')}
                className="btn-primary w-full justify-center mt-4"
              >
                Upgrade to Pro
              </button>
            )}
          </div>

          {/* Danger zone */}
          <div className="card border-red-100">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={15} className="text-red-500" />
              <p className="text-sm font-semibold text-red-600">Danger Zone</p>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Disconnecting your store will stop all data syncing. Your historical data will be retained.
            </p>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="btn text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 text-sm w-full justify-center"
            >
              Disconnect Store
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}
