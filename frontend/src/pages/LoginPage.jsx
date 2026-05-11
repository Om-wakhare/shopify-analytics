import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Zap, ArrowRight, Store, ShieldCheck, BarChart3, TrendingUp, RefreshCw } from 'lucide-react'

const FEATURES = [
  { icon: BarChart3,  title: 'CLTV & Cohort Analysis',  desc: 'Understand lifetime value and retention by cohort' },
  { icon: TrendingUp, title: 'Revenue Intelligence',     desc: 'AOV trends, repeat rate, and revenue forecasting' },
  { icon: RefreshCw,  title: 'Real-time Sync',           desc: 'Webhooks + hourly sync keep your data fresh' },
  { icon: ShieldCheck,title: 'Secure & Private',         desc: 'Data isolated per store, JWT-authenticated access' },
]

export default function LoginPage() {
  const [shop, setShop]       = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const navigate              = useNavigate()
  const [params]              = useSearchParams()
  const urlError              = params.get('error')

  const handleConnect = (e) => {
    e.preventDefault()
    setError('')

    let domain = shop.trim().toLowerCase()
    if (!domain) { setError('Please enter your store URL'); return }

    // Normalise: strip https://, trailing slashes
    domain = domain.replace(/^https?:\/\//, '').replace(/\/$/, '')
    if (!domain.includes('.')) domain += '.myshopify.com'
    if (!domain.endsWith('.myshopify.com')) {
      setError('Please enter a valid Shopify store URL (e.g. mystore.myshopify.com)')
      return
    }

    setLoading(true)
    const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    window.location.href = `${backendUrl}/connect-shopify?shop=${encodeURIComponent(domain)}`
  }

  return (
    <div className="min-h-screen flex">
      {/* Left — branding panel */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12"
           style={{ background: 'linear-gradient(145deg, #0f0d1a 0%, #1e1a3a 100%)' }}>
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
            <Zap size={20} className="text-white" />
          </div>
          <div>
            <p className="text-white font-bold text-lg leading-none">Analytics</p>
            <p className="text-slate-500 text-xs mt-0.5">D2C Platform</p>
          </div>
        </div>

        {/* Headline */}
        <div>
          <h1 className="text-4xl font-bold text-white leading-tight">
            Know your customers.<br />
            <span className="text-brand-400">Grow your revenue.</span>
          </h1>
          <p className="text-slate-400 mt-4 text-lg leading-relaxed">
            The analytics platform built for Shopify D2C brands — CLTV, cohorts, churn, and more.
          </p>

          {/* Features */}
          <div className="mt-10 space-y-4">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-900/60 border border-brand-700/40 flex items-center justify-center shrink-0">
                  <Icon size={15} className="text-brand-400" />
                </div>
                <div>
                  <p className="text-white text-sm font-medium">{title}</p>
                  <p className="text-slate-500 text-xs mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <p className="text-slate-600 text-xs">
          Trusted by 500+ Shopify brands · SOC 2 compliant · 14-day free trial
        </p>
      </div>

      {/* Right — login form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <span className="font-bold text-slate-800">Analytics Platform</span>
          </div>

          <h2 className="text-2xl font-bold text-slate-800">Connect your store</h2>
          <p className="text-slate-500 mt-2 text-sm">
            Enter your Shopify store URL to get started. You'll be redirected to Shopify to authorise access.
          </p>

          {/* Error from URL params */}
          {urlError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
              {urlError === 'invalid_state'   && 'Session expired. Please try again.'}
              {urlError === 'hmac_failed'     && 'Security check failed. Please try again.'}
              {urlError === 'token_exchange_failed' && 'Failed to connect to Shopify. Please retry.'}
              {!['invalid_state','hmac_failed','token_exchange_failed'].includes(urlError) && 'Something went wrong. Please try again.'}
            </div>
          )}

          <form onSubmit={handleConnect} className="mt-8">
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Shopify store URL
            </label>
            <div className="flex items-center bg-white border border-slate-200 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-brand-500 focus-within:border-brand-500 transition-all">
              <div className="flex items-center gap-2 px-3 border-r border-slate-100 h-12 shrink-0">
                <Store size={16} className="text-slate-400" />
              </div>
              <input
                type="text"
                value={shop}
                onChange={(e) => setShop(e.target.value)}
                placeholder="mystore.myshopify.com"
                className="flex-1 px-3 h-12 text-sm text-slate-800 placeholder-slate-400 outline-none bg-transparent"
                autoFocus
              />
            </div>
            {error && <p className="text-red-500 text-xs mt-1.5">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 h-12 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl flex items-center justify-center gap-2 transition-all active:scale-98 disabled:opacity-60"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Redirecting to Shopify…
                </>
              ) : (
                <>
                  Connect with Shopify
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Trial callout */}
          <div className="mt-6 p-4 bg-brand-50 border border-brand-100 rounded-xl">
            <p className="text-brand-700 text-sm font-medium">✨ 14-day free trial</p>
            <p className="text-brand-600/70 text-xs mt-1">
              No credit card required. Full access to all features during the trial.
            </p>
          </div>

          <p className="text-center text-xs text-slate-400 mt-6">
            By connecting, you agree to our{' '}
            <span className="underline cursor-pointer">Terms of Service</span>{' '}
            and{' '}
            <span className="underline cursor-pointer">Privacy Policy</span>.
          </p>
        </div>
      </div>
    </div>
  )
}
