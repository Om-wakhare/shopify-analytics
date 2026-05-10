import { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle, XCircle, AlertTriangle, X } from 'lucide-react'
import clsx from 'clsx'

const ToastContext = createContext(null)

const ICONS = {
  success: <CheckCircle size={16} className="text-emerald-500 shrink-0" />,
  error:   <XCircle size={16} className="text-red-500 shrink-0" />,
  warning: <AlertTriangle size={16} className="text-amber-500 shrink-0" />,
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const toast = useCallback((message, type = 'success', duration = 4000) => {
    const id = Date.now()
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), duration)
  }, [])

  const remove = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={clsx(
              'flex items-start gap-2.5 px-4 py-3 rounded-2xl shadow-lg border text-sm font-medium animate-slide-up',
              t.type === 'success' && 'bg-white border-emerald-100 text-slate-700',
              t.type === 'error'   && 'bg-white border-red-100 text-slate-700',
              t.type === 'warning' && 'bg-white border-amber-100 text-slate-700',
            )}
          >
            {ICONS[t.type]}
            <span className="flex-1">{t.message}</span>
            <button onClick={() => remove(t.id)} className="text-slate-400 hover:text-slate-600">
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)
