import { useState, useEffect, useRef, useCallback } from 'react'
import { Search, Users, ShoppingBag, ShoppingCart, X, ArrowRight, Loader } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { fetchSearch } from '../../api/client.js'
import { fmt } from '../../utils/formatters.js'
import clsx from 'clsx'

function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

const CATEGORY_META = {
  customer: { icon: Users,        label: 'Customers', color: 'text-brand-600',   bg: 'bg-brand-50' },
  product:  { icon: ShoppingBag,  label: 'Products',  color: 'text-emerald-600', bg: 'bg-emerald-50' },
  order:    { icon: ShoppingCart, label: 'Orders',    color: 'text-sky-600',     bg: 'bg-sky-50' },
}

export default function SearchModal({ isOpen, onClose }) {
  const [query, setQuery]       = useState('')
  const [results, setResults]   = useState(null)
  const [loading, setLoading]   = useState(false)
  const [active, setActive]     = useState(0)
  const inputRef                = useRef(null)
  const navigate                = useNavigate()
  const debouncedQuery          = useDebounce(query, 300)

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setResults(null)
      setActive(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  // Fetch results
  useEffect(() => {
    if (!debouncedQuery.trim()) { setResults(null); return }
    setLoading(true)
    fetchSearch(debouncedQuery)
      .then(setResults)
      .catch(() => setResults(null))
      .finally(() => setLoading(false))
  }, [debouncedQuery])

  // Flatten results for keyboard nav
  const allResults = results
    ? [
        ...results.customers.map(r => ({ ...r, type: 'customer' })),
        ...results.products.map(r  => ({ ...r, type: 'product' })),
        ...results.orders.map(r    => ({ ...r, type: 'order' })),
      ]
    : []

  const handleSelect = useCallback((item) => {
    if (item.type === 'customer') navigate('/cltv')
    if (item.type === 'product')  navigate('/products')
    if (item.type === 'order')    navigate('/revenue')
    onClose()
  }, [navigate, onClose])

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') { onClose(); return }
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive(a => Math.min(a + 1, allResults.length - 1)) }
    if (e.key === 'ArrowUp')   { e.preventDefault(); setActive(a => Math.max(a - 1, 0)) }
    if (e.key === 'Enter' && allResults[active]) handleSelect(allResults[active])
  }

  if (!isOpen) return null

  const hasResults = results && (results.customers.length + results.products.length + results.orders.length) > 0
  const categories = results
    ? [
        { key: 'customers', items: results.customers, meta: CATEGORY_META.customer },
        { key: 'products',  items: results.products,  meta: CATEGORY_META.product  },
        { key: 'orders',    items: results.orders,     meta: CATEGORY_META.order    },
      ].filter(c => c.items.length > 0)
    : []

  let flatIndex = 0

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed left-1/2 top-[15%] -translate-x-1/2 z-50 w-full max-w-xl animate-scale-in"
           style={{ filter: 'drop-shadow(0 25px 60px rgba(0,0,0,.25))' }}>
        <div className="bg-white rounded-2xl overflow-hidden" style={{ border: '1px solid rgba(226,232,240,0.8)' }}>

          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-100">
            {loading
              ? <Loader size={16} className="text-brand-500 animate-spin shrink-0" />
              : <Search size={16} className="text-slate-400 shrink-0" />
            }
            <input
              ref={inputRef}
              value={query}
              onChange={e => { setQuery(e.target.value); setActive(0) }}
              onKeyDown={handleKeyDown}
              placeholder="Search customers, products, orders…"
              className="flex-1 text-sm text-slate-800 placeholder-slate-400 outline-none bg-transparent"
            />
            {query && (
              <button onClick={() => { setQuery(''); setResults(null) }} className="text-slate-400 hover:text-slate-600">
                <X size={14} />
              </button>
            )}
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium text-slate-400 bg-slate-100 rounded-lg">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div className="max-h-[400px] overflow-y-auto">
            {!query && (
              <div className="py-10 text-center">
                <Search size={24} className="text-slate-200 mx-auto mb-2" />
                <p className="text-sm text-slate-400">Start typing to search</p>
                <p className="text-xs text-slate-300 mt-1">Customers, products, orders</p>
              </div>
            )}

            {query && !loading && !hasResults && (
              <div className="py-10 text-center">
                <p className="text-sm text-slate-500">No results for <strong>"{query}"</strong></p>
                <p className="text-xs text-slate-400 mt-1">Try a different search term</p>
              </div>
            )}

            {categories.map(({ key, items, meta }) => {
              const Icon = meta.icon
              return (
                <div key={key}>
                  <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 border-b border-slate-100">
                    <Icon size={12} className={meta.color} />
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">{meta.label}</span>
                  </div>
                  {items.map((item) => {
                    const currentIndex = flatIndex++
                    const isActive = currentIndex === active
                    return (
                      <button
                        key={item.id}
                        onClick={() => handleSelect(item)}
                        onMouseEnter={() => setActive(currentIndex)}
                        className={clsx(
                          'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                          isActive ? 'bg-brand-50' : 'hover:bg-slate-50',
                        )}
                      >
                        <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center shrink-0', meta.bg)}>
                          <Icon size={14} className={meta.color} />
                        </div>
                        <div className="flex-1 min-w-0">
                          {item.type === 'customer' && (
                            <>
                              <p className="text-sm font-medium text-slate-800 truncate">{item.email}</p>
                              <p className="text-xs text-slate-400">{item.orders_count} orders · {fmt.currency(item.total_spent)}</p>
                            </>
                          )}
                          {item.type === 'product' && (
                            <>
                              <p className="text-sm font-medium text-slate-800 truncate">{item.title}</p>
                              <p className="text-xs text-slate-400">{item.vendor}</p>
                            </>
                          )}
                          {item.type === 'order' && (
                            <>
                              <p className="text-sm font-medium text-slate-800">Order {item.order_number}</p>
                              <p className="text-xs text-slate-400">{fmt.currency(item.total_price)} · {item.financial_status}</p>
                            </>
                          )}
                        </div>
                        <ArrowRight size={14} className={clsx('shrink-0 transition-opacity', isActive ? 'text-brand-500 opacity-100' : 'opacity-0')} />
                      </button>
                    )
                  })}
                </div>
              )
            })}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-t border-slate-100">
            <div className="flex items-center gap-3 text-[11px] text-slate-400">
              <span className="flex items-center gap-1"><kbd className="bg-white border border-slate-200 rounded px-1 py-0.5 text-[10px]">↑↓</kbd> navigate</span>
              <span className="flex items-center gap-1"><kbd className="bg-white border border-slate-200 rounded px-1 py-0.5 text-[10px]">↵</kbd> select</span>
            </div>
            <span className="text-[11px] text-slate-400">
              {allResults.length > 0 ? `${allResults.length} results` : ''}
            </span>
          </div>
        </div>
      </div>
    </>
  )
}
