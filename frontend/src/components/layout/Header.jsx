import { useState, useEffect, useRef } from 'react'
import { Search, Bell, ChevronDown, User, Settings, CreditCard, LogOut } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useStore } from '../../context/StoreContext.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import SyncStatus from '../ui/SyncStatus.jsx'
import SearchModal from '../ui/SearchModal.jsx'
import clsx from 'clsx'

const ROUTE_LABELS = {
  '/':          ['Overview',          'Store-wide performance'],
  '/revenue':   ['Revenue',           'Revenue breakdown and trends'],
  '/cltv':      ['CLTV',              'Customer lifetime value'],
  '/cohorts':   ['Cohort Retention',  'Monthly retention analysis'],
  '/churn':     ['Churn',             'At-risk customers'],
  '/products':  ['Products',          'Product performance'],
  '/repeat':    ['Repeat Rate',       'Purchase frequency'],
  '/profile':   ['Profile',           'Store and account details'],
  '/settings':  ['Settings',          'Configure your workspace'],
  '/subscribe': ['Subscription',      'Manage your plan'],
}

export default function Header() {
  const { store }              = useStore()
  const { user, logout }       = useAuth()
  const navigate               = useNavigate()
  const location               = useLocation()
  const [searchOpen, setSearch] = useState(false)
  const [menuOpen, setMenu]    = useState(false)
  const menuRef                = useRef(null)

  const [title, subtitle] = ROUTE_LABELS[location.pathname] || ['Dashboard', '']

  // Cmd+K shortcut
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setSearch(true)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Close menu on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenu(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }

  const initial  = (store.domain?.[0] || 'S').toUpperCase()
  const subStatus = user?.subscription_status || 'trial'
  const subColor  = subStatus === 'active' ? '#34d399' : subStatus === 'trial' ? '#facc15' : '#f87171'

  return (
    <>
      <header
        className="h-16 flex items-center justify-between px-6 sticky top-0 z-20"
        style={{ background: 'rgba(244,246,251,0.85)', backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(226,232,240,0.6)' }}
      >
        {/* Left — breadcrumb */}
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-0.5">
            <span>Analytics</span>
            <span>/</span>
            <span className="text-brand-600 font-medium">{title}</span>
          </div>
          {subtitle && <p className="text-[11px] text-slate-400 leading-none">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-2">
          {/* Search trigger */}
          <button
            onClick={() => setSearch(true)}
            className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm text-slate-400 transition-all"
            style={{ background: 'white', border: '1px solid #e2e8f0', minWidth: 180 }}
          >
            <Search size={13} />
            <span className="flex-1 text-left text-xs">Search…</span>
            <kbd className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded-md font-medium">⌘K</kbd>
          </button>

          {/* Mobile search */}
          <button
            onClick={() => setSearch(true)}
            className="md:hidden w-8 h-8 flex items-center justify-center rounded-xl text-slate-500 hover:bg-white transition-colors"
          >
            <Search size={15} />
          </button>

          {/* Sync */}
          <SyncStatus />

          {/* Notifications */}
          <button className="relative w-8 h-8 flex items-center justify-center rounded-xl text-slate-400 hover:bg-white hover:text-slate-600 transition-colors">
            <Bell size={14} />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-brand-500 rounded-full ring-2 ring-transparent" style={{ boxShadow: '0 0 5px #7c3aed' }} />
          </button>

          {/* Avatar dropdown */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenu(v => !v)}
              className={clsx(
                'flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-xl transition-all',
                menuOpen ? 'bg-white shadow-sm' : 'hover:bg-white',
              )}
              style={{ border: '1px solid transparent', ...(menuOpen && { borderColor: '#e2e8f0' }) }}
            >
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0"
                style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)' }}
              >
                {initial}
              </div>
              <div className="hidden sm:block text-left min-w-0">
                <p className="text-xs font-semibold text-slate-700 truncate max-w-[100px] leading-none">
                  {store.domain?.split('.')[0]}
                </p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: subColor }} />
                  <span className="text-[10px] text-slate-400 capitalize">{subStatus}</span>
                </div>
              </div>
              <ChevronDown size={12} className={clsx('text-slate-400 transition-transform', menuOpen && 'rotate-180')} />
            </button>

            {/* Dropdown menu */}
            {menuOpen && (
              <div
                className="absolute right-0 top-full mt-2 w-52 bg-white rounded-2xl shadow-xl z-50 overflow-hidden animate-scale-in"
                style={{ border: '1px solid rgba(226,232,240,0.8)' }}
              >
                {/* Store info header */}
                <div className="px-4 py-3 border-b border-slate-100">
                  <p className="text-xs font-semibold text-slate-800 truncate">{store.domain}</p>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: subColor }} />
                    <span className="text-[11px] text-slate-400 capitalize">{subStatus} plan</span>
                  </div>
                </div>

                {/* Menu items */}
                {[
                  { icon: User,       label: 'Profile',      onClick: () => { navigate('/profile');   setMenu(false) } },
                  { icon: Settings,   label: 'Settings',     onClick: () => { navigate('/settings');  setMenu(false) } },
                  { icon: CreditCard, label: 'Subscription', onClick: () => { navigate('/subscribe'); setMenu(false) } },
                ].map(({ icon: Icon, label, onClick }) => (
                  <button
                    key={label}
                    onClick={onClick}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                  >
                    <Icon size={14} className="text-slate-400" />
                    {label}
                  </button>
                ))}

                <div className="border-t border-slate-100 mt-1">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 transition-colors"
                  >
                    <LogOut size={14} />
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <SearchModal isOpen={searchOpen} onClose={() => setSearch(false)} />
    </>
  )
}
