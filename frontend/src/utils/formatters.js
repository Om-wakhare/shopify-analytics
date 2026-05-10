export const fmt = {
  currency: (v, compact = false) => {
    if (v == null) return '—'
    const opts = compact && Math.abs(v) >= 1000
      ? { notation: 'compact', maximumFractionDigits: 1 }
      : { minimumFractionDigits: 2, maximumFractionDigits: 2 }
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', ...opts }).format(v)
  },
  number: (v, compact = false) => {
    if (v == null) return '—'
    if (compact && Math.abs(v) >= 1000)
      return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(v)
    return new Intl.NumberFormat('en-US').format(v)
  },
  pct: (v, decimals = 1) => v == null ? '—' : `${Number(v).toFixed(decimals)}%`,
  days: (v) => v == null ? '—' : `${Math.round(v)}d`,
  month: (v) => {
    if (!v) return '—'
    const d = new Date(v)
    return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
  },
  monthFull: (v) => {
    if (!v) return '—'
    const d = new Date(v)
    return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  },
}

export function delta(current, previous) {
  if (!previous || previous === 0) return null
  return ((current - previous) / previous) * 100
}

export function trendLabel(pct) {
  if (pct == null) return null
  return pct >= 0 ? `+${pct.toFixed(1)}%` : `${pct.toFixed(1)}%`
}
