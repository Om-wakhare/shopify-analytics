import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import clsx from 'clsx'

const THEMES = {
  brand:   { bg: 'from-violet-500/10 to-violet-500/5',  icon: 'bg-violet-500/15 text-violet-600',  accent: '#7c3aed', border: 'border-violet-200/50' },
  emerald: { bg: 'from-emerald-500/10 to-emerald-500/5', icon: 'bg-emerald-500/15 text-emerald-600', accent: '#059669', border: 'border-emerald-200/50' },
  sky:     { bg: 'from-sky-500/10 to-sky-500/5',        icon: 'bg-sky-500/15 text-sky-600',        accent: '#0284c7', border: 'border-sky-200/50' },
  amber:   { bg: 'from-amber-500/10 to-amber-500/5',    icon: 'bg-amber-500/15 text-amber-600',    accent: '#d97706', border: 'border-amber-200/50' },
  rose:    { bg: 'from-rose-500/10 to-rose-500/5',      icon: 'bg-rose-500/15 text-rose-600',      accent: '#e11d48', border: 'border-rose-200/50' },
}

export default function KPICard({ label, value, subValue, trend, trendLabel, icon: Icon, color = 'brand', loading }) {
  const t = THEMES[color] || THEMES.brand
  const up = trend > 0, dn = trend < 0

  if (loading) return (
    <div className="card overflow-hidden">
      <div className="flex items-start justify-between mb-4">
        <div className="skeleton h-3 w-24 rounded" />
        <div className="skeleton w-10 h-10 rounded-xl" />
      </div>
      <div className="skeleton h-8 w-32 rounded mb-2" />
      <div className="skeleton h-3 w-20 rounded" />
    </div>
  )

  return (
    <div
      className={clsx(
        'card card-hover overflow-hidden relative',
        t.border,
      )}
    >
      {/* Gradient accent background */}
      <div className={clsx('absolute inset-0 bg-gradient-to-br opacity-60', t.bg)} />

      <div className="relative">
        {/* Top row */}
        <div className="flex items-start justify-between mb-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
          {Icon && (
            <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center', t.icon)}>
              <Icon size={18} />
            </div>
          )}
        </div>

        {/* Value */}
        <p className="text-2xl font-bold text-slate-900 leading-none mb-1.5">{value}</p>

        {/* Sub value */}
        {subValue && <p className="text-xs text-slate-400 leading-none mb-3">{subValue}</p>}

        {/* Trend */}
        {trend != null && (
          <div className="flex items-center gap-2">
            <span className={clsx(
              'inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-lg',
              up && 'stat-up',
              dn && 'stat-down',
              !up && !dn && 'stat-flat',
            )}>
              {up && <TrendingUp size={10} />}
              {dn && <TrendingDown size={10} />}
              {!up && !dn && <Minus size={10} />}
              {trendLabel}
            </span>
            <span className="text-[11px] text-slate-400">vs last period</span>
          </div>
        )}

        {/* Bottom accent line */}
        <div
          className="absolute bottom-0 left-0 right-0 h-0.5 opacity-40"
          style={{ background: `linear-gradient(90deg, ${t.accent}, transparent)` }}
        />
      </div>
    </div>
  )
}
