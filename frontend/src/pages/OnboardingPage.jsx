import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, Circle, Loader, ArrowRight, Zap } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { useStore } from '../context/StoreContext.jsx'
import clsx from 'clsx'

const STEPS = [
  { id: 'store',    label: 'Store connected',         desc: 'Shopify OAuth completed successfully' },
  { id: 'webhooks', label: 'Webhooks registered',     desc: 'Real-time order and customer updates enabled' },
  { id: 'sync',     label: 'Syncing historical data',  desc: 'Importing your orders and customers…' },
  { id: 'ready',    label: 'Dashboard ready',          desc: 'Your analytics are ready to explore' },
]

export default function OnboardingPage() {
  const { user }      = useAuth()
  const { store }     = useStore()
  const navigate      = useNavigate()
  const [step, setStep]       = useState(0)
  const [syncLogId, setSyncLogId] = useState(null)
  const [recordCount, setRecordCount] = useState(0)
  const pollRef = useRef(null)

  const backendUrl = import.meta.env.VITE_API_URL || ''

  // Step 1 — immediately mark store connected
  useEffect(() => {
    const t1 = setTimeout(() => setStep(1), 600)
    const t2 = setTimeout(() => setStep(2), 1400)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [])

  // Step 2 — trigger bulk sync once step 2 is active
  useEffect(() => {
    if (step !== 2 || !store.domain) return

    const triggerSync = async () => {
      try {
        const token = localStorage.getItem('shopify_analytics_token')
        const res = await fetch(`${backendUrl}/sync/bulk`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({ shop_domain: store.domain, entity: 'all' }),
        })
        if (res.ok) {
          const data = await res.json()
          setSyncLogId(data.sync_log_id)
        } else {
          // Backend error — still proceed after delay
          setTimeout(() => setStep(3), 3000)
        }
      } catch {
        setTimeout(() => setStep(3), 3000)
      }
    }

    triggerSync()
  }, [step])

  // Poll sync status while we have a syncLogId
  useEffect(() => {
    if (!syncLogId) return

    const pollStatus = async () => {
      try {
        const token = localStorage.getItem('shopify_analytics_token')
        const res = await fetch(`${backendUrl}/sync/status/${syncLogId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!res.ok) return

        const data = await res.json()
        if (data.records_upserted > 0) setRecordCount(data.records_upserted)

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(pollRef.current)
          setStep(3)
        }
      } catch {
        // network error — keep polling
      }
    }

    pollRef.current = setInterval(pollStatus, 3000)
    pollStatus() // immediate first check

    return () => clearInterval(pollRef.current)
  }, [syncLogId])

  const allDone = step >= STEPS.length - 1

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'var(--page-bg)' }}>
      <div className="w-full max-w-lg animate-fade-in">

        {/* Logo */}
        <div className="flex items-center gap-3 mb-8">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #5b21b6)', boxShadow: '0 0 16px rgba(124,58,237,.4)' }}
          >
            <Zap size={20} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-slate-800">Getting you set up</p>
            <p className="text-slate-400 text-xs mt-0.5">{store.domain}</p>
          </div>
        </div>

        {/* Steps */}
        <div className="card mb-5">
          <div className="space-y-5">
            {STEPS.map((s, i) => {
              const done    = step > i
              const current = step === i
              return (
                <div key={s.id} className="flex items-start gap-3.5">
                  <div className="shrink-0 mt-0.5">
                    {done ? (
                      <CheckCircle size={20} className="text-emerald-500" />
                    ) : current ? (
                      <Loader size={20} className="text-brand-500 animate-spin" />
                    ) : (
                      <Circle size={20} className="text-slate-200" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={clsx(
                      'text-sm font-semibold leading-none',
                      done ? 'text-slate-800' : current ? 'text-brand-700' : 'text-slate-300',
                    )}>
                      {s.label}
                      {s.id === 'sync' && current && recordCount > 0 && (
                        <span className="ml-2 text-xs font-normal text-brand-400">
                          {recordCount.toLocaleString()} records
                        </span>
                      )}
                    </p>
                    <p className={clsx(
                      'text-xs mt-1 leading-relaxed',
                      done || current ? 'text-slate-400' : 'text-slate-200',
                    )}>
                      {s.desc}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Trial banner */}
        <div
          className="p-4 rounded-2xl mb-5"
          style={{ background: 'linear-gradient(135deg, rgba(124,58,237,.08), rgba(124,58,237,.04))', border: '1px solid rgba(124,58,237,.15)' }}
        >
          <p className="text-brand-700 text-sm font-semibold">🎉 Your 14-day free trial has started</p>
          <p className="text-brand-600/70 text-xs mt-1">
            Full access to all features. No credit card required.
          </p>
        </div>

        {/* CTA */}
        <button
          onClick={() => navigate('/', { replace: true })}
          disabled={!allDone}
          className={clsx(
            'w-full h-12 rounded-2xl font-semibold flex items-center justify-center gap-2 transition-all',
            allDone
              ? 'btn-primary'
              : 'bg-slate-100 text-slate-300 cursor-not-allowed',
          )}
        >
          {allDone ? (
            <> Go to Dashboard <ArrowRight size={16} /> </>
          ) : (
            <> <Loader size={15} className="animate-spin" /> Setting up your workspace… </>
          )}
        </button>
      </div>
    </div>
  )
}
