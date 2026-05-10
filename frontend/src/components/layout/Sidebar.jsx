import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, TrendingUp, Users, RefreshCw,
  ShoppingBag, BarChart3, AlertTriangle, Settings,
  Zap, ChevronDown, Store, LogOut, CreditCard,
} from 'lucide-react'
import { useState } from 'react'
import { useStore } from '../../context/StoreContext.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import clsx from 'clsx'

const NAV = [
  { to: '/',         icon: LayoutDashboard, label: 'Overview',         color: '#a78bfa' },
  { to: '/revenue',  icon: TrendingUp,      label: 'Revenue',          color: '#34d399' },
  { to: '/cltv',     icon: Users,           label: 'CLTV',             color: '#60a5fa' },
  { to: '/cohorts',  icon: BarChart3,       label: 'Cohort Retention', color: '#f472b6' },
  { to: '/churn',    icon: AlertTriangle,   label: 'Churn',            color: '#fb923c' },
  { to: '/products', icon: ShoppingBag,     label: 'Products',         color: '#facc15' },
  { to: '/repeat',   icon: RefreshCw,       label: 'Repeat Rate',      color: '#2dd4bf' },
]

function NavItem({ to, icon: Icon, label, color }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) => clsx(
        'group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 relative',
        isActive
          ? 'text-white'
          : 'text-slate-500 hover:text-slate-300 hover:bg-white/5',
      )}
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span
              className="absolute inset-0 rounded-xl opacity-100"
              style={{ background: `linear-gradient(135deg, ${color}22, ${color}11)`, border: `1px solid ${color}33` }}
            />
          )}
          <span
            className={clsx(
              'relative w-7 h-7 rounded-lg flex items-center justify-center shrink-0 transition-all',
              isActive ? 'shadow-lg' : 'group-hover:bg-white/8',
            )}
            style={isActive ? { background: `${color}22`, color } : {}}
          >
            <Icon size={15} style={isActive ? { color } : {}} />
          </span>
          <span className="relative">{label}</span>
          {isActive && (
            <span
              className="absolute right-3 w-1.5 h-1.5 rounded-full"
              style={{ background: color, boxShadow: `0 0 6px ${color}` }}
            />
          )}
        </>
      )}
    </NavLink>
  )
}

export default function Sidebar() {
  const { store }     = useStore()
  const { user, logout } = useAuth()
  const navigate      = useNavigate()
  const [open, setOpen] = useState(false)

  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }

  const initial = (store.domain?.[0] || 'S').toUpperCase()
  const subStatus = user?.subscription_status || 'trial'

  return (
    <aside
      className="fixed inset-y-0 left-0 w-64 flex flex-col z-30 select-none"
      style={{ background: 'var(--sidebar-bg)', borderRight: '1px solid var(--sidebar-border)' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 h-16" style={{ borderBottom: '1px solid var(--sidebar-border)' }}>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: 'linear-gradient(135deg, #7c3aed, #5b21b6)', boxShadow: '0 0 12px rgba(124,58,237,.4)' }}
        >
          <Zap size={15} className="text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-sm leading-none tracking-tight">Analytics</p>
          <p className="text-slate-600 text-[10px] mt-0.5 font-medium">D2C Platform</p>
        </div>
      </div>

      {/* Store pill */}
      <div className="px-4 py-3" style={{ borderBottom: '1px solid var(--sidebar-border)' }}>
        <button
          onClick={() => setOpen(v => !v)}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl transition-colors text-left"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}
        >
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0"
            style={{ background: 'linear-gradient(135deg, #7c3aed60, #5b21b660)' }}
          >
            {initial}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-slate-200 text-xs font-semibold truncate leading-none">{store.domain}</p>
            <div className="flex items-center gap-1 mt-1">
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: subStatus === 'active' ? '#34d399' : subStatus === 'trial' ? '#facc15' : '#f87171' }}
              />
              <span className="text-slate-500 text-[10px] capitalize">{subStatus}</span>
            </div>
          </div>
          <ChevronDown size={12} className={clsx('text-slate-600 transition-transform', open && 'rotate-180')} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="text-[9px] font-bold text-slate-700 uppercase tracking-[0.15em] px-3 mb-3">Analytics</p>
        {NAV.map(item => <NavItem key={item.to} {...item} />)}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-3 space-y-0.5" style={{ borderTop: '1px solid var(--sidebar-border)' }}>
        <NavItem to="/settings"   icon={Settings}    label="Settings"      color="#94a3b8" />
        <NavItem to="/subscribe"  icon={CreditCard}  label="Subscription"  color="#34d399" />

        {/* User row */}
        <div className="flex items-center gap-2.5 px-3 py-2.5 mt-1 rounded-xl"
             style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)' }}
          >
            {initial}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-slate-300 text-xs font-semibold truncate leading-none">{store.domain?.split('.')[0] || 'Store'}</p>
            <p className="text-slate-600 text-[10px] mt-0.5 truncate capitalize">{subStatus} plan</p>
          </div>
          <button
            onClick={handleLogout}
            title="Sign out"
            className="w-6 h-6 rounded-lg flex items-center justify-center text-slate-600 hover:text-red-400 hover:bg-red-400/10 transition-all"
          >
            <LogOut size={12} />
          </button>
        </div>
      </div>
    </aside>
  )
}
