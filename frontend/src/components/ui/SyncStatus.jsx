import { useState } from 'react'
import { RefreshCw, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { useStore } from '../../context/StoreContext.jsx'
import { useQueryClient } from '@tanstack/react-query'
import { useToast } from './Toast.jsx'
import clsx from 'clsx'

export default function SyncStatus() {
  const { store } = useStore()
  const qc        = useQueryClient()
  const toast     = useToast()
  const [syncing, setSyncing] = useState(false)
  const [lastSync, setLastSync] = useState(null)
  const [syncError, setSyncError] = useState(false)

  const triggerSync = async () => {
    setSyncing(true)
    setSyncError(false)
    try {
      const backendUrl = import.meta.env.VITE_API_URL || ''
      const res = await fetch(`${backendUrl}/sync/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shop_domain: store.domain, entity: 'all' }),
      })
      if (!res.ok) throw new Error('Sync failed')
      const data = await res.json()
      toast(`Sync queued — ID: ${data.sync_log_id?.slice(0, 8)}`, 'success')
      setLastSync(new Date())
      // Invalidate all KPI queries after 30s
      setTimeout(() => qc.invalidateQueries(), 30000)
    } catch (e) {
      setSyncError(true)
      toast('Sync failed — check Celery worker', 'error')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      {lastSync && !syncError && (
        <span className="hidden md:flex items-center gap-1 text-xs text-slate-400">
          <CheckCircle size={11} className="text-emerald-500" />
          Synced {lastSync.toLocaleTimeString()}
        </span>
      )}
      {syncError && (
        <span className="flex items-center gap-1 text-xs text-red-500">
          <AlertCircle size={11} />
          Sync failed
        </span>
      )}
      <button
        onClick={triggerSync}
        disabled={syncing}
        title="Sync latest data from Shopify"
        className={clsx(
          'flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all',
          syncing
            ? 'bg-brand-50 text-brand-500 cursor-wait'
            : 'bg-brand-600 text-white hover:bg-brand-700 active:scale-95',
        )}
      >
        <RefreshCw size={12} className={clsx(syncing && 'animate-spin')} />
        {syncing ? 'Syncing…' : 'Sync Now'}
      </button>
    </div>
  )
}
