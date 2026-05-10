export function ChartSkeleton({ height = 320 }) {
  return (
    <div className="card" style={{ height }}>
      <div className="skeleton h-4 w-32 rounded mb-1.5" />
      <div className="skeleton h-3 w-48 rounded mb-6" />
      <div className="flex items-end gap-2" style={{ height: height - 100 }}>
        {Array.from({ length: 12 }, (_, i) => (
          <div
            key={i}
            className="flex-1 rounded-t skeleton"
            style={{ height: `${30 + Math.sin(i) * 20 + Math.random() * 40}%` }}
          />
        ))}
      </div>
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <div className="skeleton h-3 w-24 rounded" />
          <div className="skeleton h-7 w-32 rounded mt-3" />
          <div className="skeleton h-3 w-20 rounded" />
        </div>
        <div className="skeleton w-10 h-10 rounded-xl" />
      </div>
    </div>
  )
}

export function TableSkeleton({ rows = 8 }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }, (_, i) => (
        <div
          key={i}
          className="skeleton h-11 rounded-xl"
          style={{ opacity: 1 - i * 0.08 }}
        />
      ))}
    </div>
  )
}

export function ErrorCard({ message }) {
  return (
    <div className="card border-red-100 bg-red-50/50 text-center py-10">
      <p className="text-sm font-semibold text-red-600">Failed to load data</p>
      <p className="text-xs text-red-400 mt-1">{message}</p>
    </div>
  )
}
