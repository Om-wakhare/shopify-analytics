import { Bell, Search } from 'lucide-react'
import { useStore } from '../../context/StoreContext.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import SyncStatus from '../ui/SyncStatus.jsx'

export default function Header({ title, subtitle }) {
  const { store } = useStore()
  const { user }  = useAuth()

  const subStatus = user?.subscription_status || 'trial'
  const subColor  = subStatus === 'active' ? '#34d399' : subStatus === 'trial' ? '#facc15' : '#f87171'

  return (
    <header className="h-16 flex items-center justify-between px-6 bg-white/80 backdrop-blur-sm sticky top-0 z-20"
            style={{ borderBottom: '1px solid rgba(226,232,240,0.8)' }}>
      <div>
        <h1 className="text-base font-bold text-slate-800 leading-none">{title}</h1>
        {subtitle && <p className="text-[11px] text-slate-400 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-2.5">
        {/* Search */}
        <div className="hidden md:flex items-center gap-2 rounded-xl px-3 py-1.5 w-48 transition-all"
             style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}>
          <Search size={12} className="text-slate-400" />
          <input
            type="text"
            placeholder="Search…"
            className="bg-transparent text-xs text-slate-600 placeholder-slate-400 outline-none w-full"
          />
        </div>

        {/* Sync */}
        <SyncStatus />

        {/* Notifications */}
        <button className="relative w-8 h-8 flex items-center justify-center rounded-xl text-slate-400 hover:bg-slate-100 transition-colors">
          <Bell size={14} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-brand-500 rounded-full ring-2 ring-white" />
        </button>

        {/* Store badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium"
             style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}>
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: subColor, boxShadow: `0 0 5px ${subColor}` }} />
          <span className="text-slate-600 truncate max-w-[140px]">{store.domain}</span>
        </div>
      </div>
    </header>
  )
}
