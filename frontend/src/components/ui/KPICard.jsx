import { useEffect, useRef, useState } from 'react'
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react'
import clsx from 'clsx'

const THEMES = {
  brand:   { bg: 'from-violet-500/10 via-violet-500/5 to-transparent', icon: 'bg-violet-100 text-violet-600',   accent: '#7c3aed', border: 'border-violet-200/50', glow: 'rgba(124,58,237,.12)' },
  emerald: { bg: 'from-emerald-500/10 via-emerald-500/5 to-transparent', icon: 'bg-emerald-100 text-emerald-600', accent: '#059669', border: 'border-emerald-200/50', glow: 'rgba(5,150,105,.10)' },
  sky:     { bg: 'from-sky-500/10 via-sky-500/5 to-transparent',       icon: 'bg-sky-100 text-sky-600',          accent: '#0284c7', border: 'border-sky-200/50',     glow: 'rgba(2,132,199,.10)' },
  amber:   { bg: 'from-amber-500/10 via-amber-500/5 to-transparent',   icon: 'bg-amber-100 text-amber-600',      accent: '#d97706', border: 'border-amber-200/50',   glow: 'rgba(217,119,6,.10)' },
  rose:    { bg: 'from-rose-500/10 via-rose-500/5 to-transparent',     icon: 'bg-rose-100 text-rose-600',        accent: '#e11d48', border: 'border-rose-200/50',    glow: 'rgba(225,29,72,.10)' },
}

const TOOLTIPS = {
  'Total Revenue':           'Sum of all paid orders in USD',
  'Avg Order Value':         'Total revenue ÷ number of paid orders',
  'Repeat Order Rate':       '% of customers who ordered more than once',
  'Avg CLTV':                'Average revenue per customer, all time',
  'Avg Time Between Orders': 'Average days between purchases for repeat buyers',
  'Total Customers':         'Unique customers who have placed at least one order',
  'Total Orders':            'All paid, non-cancelled orders',
  'Proj. 12M CLTV':          'Projected revenue per customer over the next 12 months',
}

function useCountUp(target, duration = 800) {
  const [value, setValue] = useState(0)
  const frameRef = useRef(null)

  useEffect(() => {
    if (target == null || isNaN(parseFloat(String(target).replace(/[^0-9.-]/g, '')))) {
      setValue(target)
      return
    }
    const numericTarget = parseFloat(String(target).replace(/[^0-9.-]/g, ''))
    const start = performance.now()
    const animate = (now) => {
      const progress = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(numericTarget * eased * 100) / 100)
      if (progress < 1) frameRef.current = requestAnimationFrame(animate)
    }
    frameRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frameRef.current)
  }, [target, duration])

  return value
}

export default function KPICard({ label, value, subValue, trend, trendLabel, icon: Icon, color = 'brand', loading, tooltip }) {
  const t = THEMES[color] || THEMES.brand
  const up = trend > 0
  const dn = trend < 0
  const [showTip, setShowTip] = useState(false)
  const tip = tooltip || TOOLTIPS[label]

  if (loading) return (
    <div className="card overflow-hidden" style={{ border: `1px solid rgba(226,232,240,0.7)` }}>
      <div className="flex items-start justify-between mb-4">
        <div className="skeleton h-3 w-24 rounded" />
        <div className="skeleton w-10 h-10 rounded-xl" />
      </div>
      <div className="skeleton h-8 w-28 rounded mb-2" />
      <div className="skeleton h-3 w-20 rounded mb-3" />
      <div className="skeleton h-3 w-28 rounded" />
    </div>
  )

  return (
    <div
      className={clsx('card card-hover overflow-hidden relative group', t.border)}
      style={{ border: `1px solid`, borderColor: 'rgba(226,232,240,0.7)' }}
      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = `0 8px 32px ${t.glow}, 0 2px 8px rgba(0,0,0,.06)` }}
      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '' }}
    >
      {/* Gradient bg */}
      <div className={clsx('absolute inset-0 bg-gradient-to-br pointer-events-none', t.bg)} />

      <div className="relative">
        {/* Top row */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-1.5">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">{label}</p>
            {tip && (
              <div className="relative">
                <Info
                  size={11}
                  className="text-slate-300 hover:text-slate-500 cursor-help transition-colors"
                  onMouseEnter={() => setShowTip(true)}
                  onMouseLeave={() => setShowTip(false)}
                />
                {showTip && (
                  <div className="absolute left-0 bottom-full mb-1.5 w-44 bg-slate-800 text-white text-[10px] rounded-lg px-2.5 py-2 shadow-xl z-10 leading-relaxed">
                    {tip}
                  </div>
                )}
              </div>
            )}
          </div>
          {Icon && (
            <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center shrink-0', t.icon)}>
              <Icon size={18} />
            </div>
          )}
        </div>

        {/* Value */}
        <p className="text-2xl font-extrabold text-slate-900 leading-none mb-1.5 tracking-tight animate-count-up">
          {value ?? '—'}
        </p>

        {/* Sub value */}
        {subValue && <p className="text-[11px] text-slate-400 leading-none mb-3">{subValue}</p>}

        {/* Trend */}
        {trend != null && (
          <div className="flex items-center gap-2">
            <span className={clsx(up && 'stat-up', dn && 'stat-down', !up && !dn && 'stat-flat')}>
              {up && <TrendingUp size={9} />}
              {dn && <TrendingDown size={9} />}
              {!up && !dn && <Minus size={9} />}
              {trendLabel}
            </span>
            <span className="text-[10px] text-slate-400">vs last period</span>
          </div>
        )}

        {/* Bottom accent bar */}
        <div
          className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          style={{ background: `linear-gradient(90deg, ${t.accent}, transparent)` }}
        />
      </div>
    </div>
  )
}
