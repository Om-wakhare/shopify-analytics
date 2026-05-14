import { BarChart3, RefreshCw, SearchX, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

const VARIANTS = {
  noData: {
    icon: BarChart3,
    title: 'No data yet',
    desc:  'Sync your Shopify store to start seeing analytics here.',
    color: 'text-brand-400',
    bg:    'bg-brand-50',
  },
  error: {
    icon: AlertTriangle,
    title: 'Failed to load',
    desc:  'Something went wrong fetching this data. Try refreshing.',
    color: 'text-red-400',
    bg:    'bg-red-50',
  },
  noResults: {
    icon: SearchX,
    title: 'No results found',
    desc:  'Try adjusting your filters or search term.',
    color: 'text-slate-400',
    bg:    'bg-slate-100',
  },
}

export default function EmptyState({
  variant = 'noData',
  title,
  description,
  action,
  onAction,
  className,
}) {
  const v    = VARIANTS[variant] || VARIANTS.noData
  const Icon = v.icon

  return (
    <div className={clsx('flex flex-col items-center justify-center py-14 px-6 text-center', className)}>
      <div className={clsx('w-14 h-14 rounded-2xl flex items-center justify-center mb-4', v.bg)}>
        <Icon size={24} className={v.color} />
      </div>
      <p className="text-sm font-semibold text-slate-700 mb-1">{title || v.title}</p>
      <p className="text-xs text-slate-400 max-w-xs leading-relaxed">{description || v.desc}</p>
      {action && (
        <button
          onClick={onAction}
          className="mt-5 btn-primary text-xs gap-1.5"
        >
          <RefreshCw size={12} />
          {action}
        </button>
      )}
    </div>
  )
}
