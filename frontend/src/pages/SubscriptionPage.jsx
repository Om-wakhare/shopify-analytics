import { useState } from 'react'
import { Check, Zap, ArrowRight, Crown, Star, Rocket } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import clsx from 'clsx'

const PLANS = [
  {
    id:       'starter',
    name:     'Starter',
    price:    29,
    icon:     Rocket,
    color:    'sky',
    popular:  false,
    features: [
      '1 Shopify store',
      '6-month data history',
      'CLTV & AOV analytics',
      'Churn analysis',
      'CSV exports',
      'Email support',
    ],
  },
  {
    id:       'growth',
    name:     'Growth',
    price:    79,
    icon:     Star,
    color:    'brand',
    popular:  true,
    features: [
      'Up to 3 Shopify stores',
      '12-month data history',
      'Everything in Starter',
      'Cohort retention analysis',
      'Product performance',
      'Priority support',
    ],
  },
  {
    id:       'pro',
    name:     'Pro',
    price:    199,
    icon:     Crown,
    color:    'amber',
    popular:  false,
    features: [
      'Unlimited stores',
      'Full data history',
      'Everything in Growth',
      'Custom date ranges',
      'API access',
      'Dedicated support',
    ],
  },
]

const COLOR = {
  sky:   { card: 'border-sky-200',    badge: 'bg-sky-50 text-sky-700',   btn: 'bg-sky-600 hover:bg-sky-700',   icon: 'bg-sky-100 text-sky-600' },
  brand: { card: 'border-brand-300',  badge: 'bg-brand-600 text-white',  btn: 'bg-brand-600 hover:bg-brand-700', icon: 'bg-brand-100 text-brand-600' },
  amber: { card: 'border-amber-200',  badge: 'bg-amber-50 text-amber-700', btn: 'bg-amber-600 hover:bg-amber-700', icon: 'bg-amber-100 text-amber-600' },
}

export default function SubscriptionPage() {
  const { user, token } = useAuth()
  const [loading, setLoading] = useState('')

  const handleSubscribe = async (planId) => {
    setLoading(planId)
    try {
      const res = await fetch(`/api/billing/subscribe?plan=${planId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (data.confirmation_url) {
        window.location.href = data.confirmation_url
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading('')
    }
  }

  const trialDaysLeft = user?.trial_ends_at
    ? Math.max(0, Math.ceil((new Date(user.trial_ends_at) - Date.now()) / 86400000))
    : null

  return (
    <div className="min-h-screen bg-slate-50 py-16 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
              <Zap size={20} className="text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-slate-800">Choose your plan</h1>
          <p className="text-slate-500 mt-3 max-w-md mx-auto">
            All plans include a 14-day free trial. Cancel anytime.
          </p>

          {trialDaysLeft !== null && trialDaysLeft > 0 && (
            <div className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-emerald-50 border border-emerald-100 rounded-full text-sm text-emerald-700 font-medium">
              <span className="w-2 h-2 bg-emerald-500 rounded-full" />
              {trialDaysLeft} days left in your free trial
            </div>
          )}
        </div>

        {/* Plan cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANS.map((plan) => {
            const c    = COLOR[plan.color]
            const Icon = plan.icon
            return (
              <div
                key={plan.id}
                className={clsx(
                  'bg-white rounded-2xl border-2 p-6 flex flex-col relative transition-shadow hover:shadow-card-hover',
                  c.card,
                  plan.popular && 'shadow-lg scale-105',
                )}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-3 py-1 bg-brand-600 text-white text-xs font-bold rounded-full uppercase tracking-wide">
                      Most Popular
                    </span>
                  </div>
                )}

                {/* Plan header */}
                <div className="flex items-center gap-3 mb-4">
                  <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center', c.icon)}>
                    <Icon size={18} />
                  </div>
                  <div>
                    <p className="font-bold text-slate-800">{plan.name}</p>
                    <p className="text-xs text-slate-400">per month</p>
                  </div>
                </div>

                {/* Price */}
                <div className="mb-6">
                  <span className="text-4xl font-bold text-slate-800">${plan.price}</span>
                  <span className="text-slate-400 text-sm">/mo</span>
                  <p className="text-xs text-slate-400 mt-1">14-day free trial included</p>
                </div>

                {/* Features */}
                <ul className="space-y-2.5 flex-1 mb-6">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-slate-600">
                      <Check size={14} className="text-emerald-500 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                <button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={!!loading}
                  className={clsx(
                    'w-full h-11 rounded-xl text-white font-semibold flex items-center justify-center gap-2 transition-all active:scale-98 disabled:opacity-60',
                    c.btn,
                  )}
                >
                  {loading === plan.id ? (
                    <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Processing…</>
                  ) : (
                    <>Start Free Trial <ArrowRight size={15} /></>
                  )}
                </button>
              </div>
            )
          })}
        </div>

        {/* Trust strip */}
        <div className="mt-12 text-center">
          <p className="text-slate-400 text-sm">
            Secure payments via Shopify Billing · Cancel anytime · No hidden fees
          </p>
        </div>
      </div>
    </div>
  )
}
