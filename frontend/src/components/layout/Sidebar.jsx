import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, TrendingUp, Users, RefreshCw,
  ShoppingBag, BarChart3, AlertTriangle, Settings,
  Zap, ChevronDown, Store, LogOut, CreditCard,
  User, PanelLeftClose, PanelLeftOpen,
} from 'lucide-react'
import { useState, useEffect } from 'react'
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

const BOTTOM_NAV = [
  { to: '/profile',   icon: User,       label: 'Profile',      color: '#94a3b8' },
  { to: '/settings',  icon: Settings,   label: 'Settings',     color: '#94a3b8' },
  { to: '/subscribe', icon: CreditCard, label: 'Subscription', color: '#34d399' },
]

function NavItem({ to, icon: Icon, label, color, collapsed }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      title={collapsed ? label : undefined}
      className={({ isActive }) => clsx(
        'group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
        collapsed && 'justify-center px-2',
        isActive
          ? 'text-white'
          : 'text-slate-500 hover:text-slate-300 hover:bg-white/5',
      )}
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span
              className="absolute inset-0 rounded-xl"
              style={{ background: `linear-gradient(135deg, ${color}25, ${color}10)`, border: `1px solid ${color}30` }}
            />
          )}
          <span
            className={clsx(
              'relative w-7 h-7 rounded-lg flex items-center justify-center shrink-0 transition-all duration-150',
              isActive && 'shadow-md',
            )}
            style={isActive ? { background: `${color}20`, color } : {}}
          >
            <Icon size={15} style={isActive ? { color } : {}} />
          </span>
          {!collapsed && <span className="relative truncate">{label}</span>}
          {isActive && !collapsed && (
            <span
              className="absolute right-3 w-1.5 h-1.5 rounded-full"
              style={{ background: color, boxShadow: `0 0 8px ${color}` }}
            />
          )}
          {/* Tooltip when collapsed */}
          {collapsed && (
            <span className="absolute left-full ml-3 px-2 py-1 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
              {label}
            </span>
          )}
        </>
      )}
    </NavLink>
  )
}

export default function Sidebar() {
  const { store }           = useStore()
  const { user, logout }    = useAuth()
  const navigate            = useNavigate()
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true')

  const toggleCollapse = () => {
    const next = !collapsed
    setCollapsed(next)
    localStorage.setItem('sidebar_collapsed', String(next))
  }

  // Ctrl+B shortcut
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') { e.preventDefault(); toggleCollapse() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [collapsed])

  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }
  const initial      = (store.domain?.[0] || 'S').toUpperCase()
  const subStatus    = user?.subscription_status || 'trial'
  const subColor     = subStatus === 'active' ? '#34d399' : subStatus === 'trial' ? '#facc15' : '#f87171'

  return (
    <aside
      className="fixed inset-y-0 left-0 flex flex-col z-30 transition-all duration-300 ease-in-out"
      style={{
        width: collapsed ? 72 : 256,
        background: 'var(--sidebar-bg)',
        borderRight: '1px solid var(--sidebar-border)',
      }}
    >
      {/* Logo + collapse toggle */}
      <div
        className="flex items-center h-16 px-4"
        style={{ borderBottom: '1px solid var(--sidebar-border)' }}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #5b21b6)', boxShadow: '0 0 16px rgba(124,58,237,.4)' }}
          >
            <Zap size={15} className="text-white" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-white font-bold text-sm leading-none tracking-tight">Analytics</p>
              <p className="text-slate-600 text-[10px] mt-0.5 font-medium">D2C Platform</p>
            </div>
          )}
        </div>
        <button
          onClick={toggleCollapse}
          title={`${collapsed ? 'Expand' : 'Collapse'} sidebar (Ctrl+B)`}
          className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-600 hover:text-slate-400 hover:bg-white/5 transition-all shrink-0"
        >
          {collapsed ? <PanelLeftOpen size={14} /> : <PanelLeftClose size={14} />}
        </button>
      </div>

      {/* Store pill */}
      {!collapsed && (
        <div className="px-4 py-3" style={{ borderBottom: '1px solid var(--sidebar-border)' }}>
          <div
            className="flex items-center gap-2.5 px-3 py-2 rounded-xl"
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
              <div className="flex items-center gap-1 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: subColor, boxShadow: `0 0 4px ${subColor}` }} />
                <span className="text-slate-500 text-[10px] capitalize">{subStatus}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className={clsx('flex-1 py-4 space-y-0.5 overflow-y-auto overflow-x-hidden', collapsed ? 'px-2' : 'px-3')}>
        {!collapsed && (
          <p className="text-[9px] font-bold text-slate-700 uppercase tracking-[0.15em] px-3 mb-3">Analytics</p>
        )}
        {NAV.map(item => <NavItem key={item.to} {...item} collapsed={collapsed} />)}
      </nav>

      {/* Bottom nav */}
      <div
        className={clsx('py-3 space-y-0.5', collapsed ? 'px-2' : 'px-3')}
        style={{ borderTop: '1px solid var(--sidebar-border)' }}
      >
        {BOTTOM_NAV.map(item => <NavItem key={item.to} {...item} collapsed={collapsed} />)}

        {/* User row */}
        {!collapsed ? (
          <div
            className="flex items-center gap-2.5 px-3 py-2.5 mt-1 rounded-xl"
            style={{ background: 'rgba(255,255,255,0.03)' }}
          >
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)' }}
            >
              {initial}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-slate-300 text-xs font-semibold truncate leading-none">{store.domain?.split('.')[0]}</p>
              <p className="text-slate-600 text-[10px] mt-0.5 capitalize">{subStatus}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="w-6 h-6 rounded-lg flex items-center justify-center text-slate-600 hover:text-red-400 hover:bg-red-400/10 transition-all"
            >
              <LogOut size={12} />
            </button>
          </div>
        ) : (
          <button
            onClick={handleLogout}
            title="Sign out"
            className="w-full flex items-center justify-center py-2.5 text-slate-600 hover:text-red-400 hover:bg-red-400/10 rounded-xl transition-all"
          >
            <LogOut size={14} />
          </button>
        )}
      </div>
    </aside>
  )
}
