import { useState, useEffect } from 'react'
import Sidebar from './Sidebar.jsx'
import Header from './Header.jsx'

export default function Layout({ children }) {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true')

  // Listen for sidebar collapse changes via localStorage
  useEffect(() => {
    const handler = () => setCollapsed(localStorage.getItem('sidebar_collapsed') === 'true')
    window.addEventListener('storage', handler)
    // Also listen for keyboard shortcut
    const keyHandler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        setTimeout(() => setCollapsed(localStorage.getItem('sidebar_collapsed') === 'true'), 50)
      }
    }
    window.addEventListener('keydown', keyHandler)
    return () => { window.removeEventListener('storage', handler); window.removeEventListener('keydown', keyHandler) }
  }, [])

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--page-bg)' }}>
      <Sidebar />
      <div
        className="flex-1 flex flex-col min-h-screen transition-all duration-300"
        style={{ marginLeft: collapsed ? 72 : 256 }}
      >
        <Header />
        <main className="flex-1 p-6 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  )
}
