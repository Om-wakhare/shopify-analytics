import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, Circle, Loader, ArrowRight, Zap } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import clsx from 'clsx'

const STEPS = [
  { id: 'store',    label: 'Store connected',         desc: 'Shopify OAuth completed successfully' },
  { id: 'webhooks', label: 'Webhooks registered',     desc: 'Real-time order and customer updates enabled' },
  { id: 'sync',     label: 'Historical data syncing', desc: 'Importing your orders and customers (this may take a few minutes)' },
  { id: 'ready',    label: 'Dashboard ready',         desc: 'Your analytics are being computed' },
]

export default function OnboardingPage() {
  const { user }    = useAuth()
  const navigate    = useNavigate()
  const [step, setStep] = useState(0)

  useEffect(() => {
    // Simulate step progression
    const timers = [
      setTimeout(() => setStep(1), 800),
      setTimeout(() => setStep(2), 1800),
      setTimeout(() => setStep(3), 3500),
    ]
    return () => timers.forEach(clearTimeout)
  }, [])

  const allDone = step >= STEPS.length - 1

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-lg animate-fade-in">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
            <Zap size={20} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-slate-800">Getting you set up</p>
            <p className="text-slate-500 text-xs">{user?.shop_domain}</p>
          </div>
        </div>

        {/* Steps */}
        <div className="card mb-6">
          <div className="space-y-4">
            {STEPS.map((s, i) => {
              const done    = step > i
              const current = step === i
              return (
                <div key={s.id} className="flex items-start gap-3">
                  <div className="shrink-0 mt-0.5">
                    {done ? (
                      <CheckCircle size={20} className="text-emerald-500" />
                    ) : current ? (
                      <Loader size={20} className="text-brand-500 animate-spin" />
                    ) : (
                      <Circle size={20} className="text-slate-200" />
                    )}
                  </div>
                  <div>
                    <p className={clsx('text-sm font-medium', done ? 'text-slate-800' : current ? 'text-brand-700' : 'text-slate-400')}>
                      {s.label}
                    </p>
                    <p className={clsx('text-xs mt-0.5', done || current ? 'text-slate-500' : 'text-slate-300')}>
                      {s.desc}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Trial info */}
        <div className="p-4 bg-brand-50 border border-brand-100 rounded-2xl mb-6">
          <p className="text-brand-700 text-sm font-semibold">🎉 Your 14-day free trial has started</p>
          <p className="text-brand-600/70 text-xs mt-1">
            Full access to all features. No credit card required until your trial ends.
          </p>
        </div>

        {/* CTA */}
        <button
          onClick={() => navigate('/', { replace: true })}
          disabled={!allDone}
          className={clsx(
            'w-full h-12 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all',
            allDone
              ? 'bg-brand-600 text-white hover:bg-brand-700 active:scale-98'
              : 'bg-slate-100 text-slate-400 cursor-not-allowed',
          )}
        >
          {allDone ? (
            <> Go to Dashboard <ArrowRight size={16} /> </>
          ) : (
            <> <Loader size={15} className="animate-spin" /> Setting up… </>
          )}
        </button>
      </div>
    </div>
  )
}
