import Sidebar from './Sidebar.jsx'
import Header from './Header.jsx'

export default function Layout({ title, subtitle, children }) {
  return (
    <div className="min-h-screen flex" style={{ background: 'var(--page-bg)' }}>
      <Sidebar />
      <div className="flex-1 flex flex-col ml-64 min-h-screen">
        <Header title={title} subtitle={subtitle} />
        <main className="flex-1 p-6 animate-fade-in max-w-[1400px] w-full">
          {children}
        </main>
      </div>
    </div>
  )
}
