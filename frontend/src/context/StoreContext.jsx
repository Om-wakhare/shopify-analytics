import { createContext, useContext, useState, useEffect } from 'react'

const StoreContext = createContext(null)

function getStoreFromToken() {
  try {
    const token = localStorage.getItem('shopify_analytics_token')
    if (!token) return null
    const payload = JSON.parse(atob(token.split('.')[1]))
    return {
      label:    payload.shop_domain,
      domain:   payload.shop_domain,
      currency: 'USD',
    }
  } catch {
    return null
  }
}

// Fallback for dev/mock mode
const DEFAULT_STORE = { label: 'Website Solution', domain: 'website-solution-ztmwqzyt.myshopify.com', currency: 'USD' }

export function StoreProvider({ children }) {
  const [store, setStore] = useState(() => getStoreFromToken() || DEFAULT_STORE)

  // Update store when token changes (e.g. after login)
  useEffect(() => {
    const fromToken = getStoreFromToken()
    if (fromToken) setStore(fromToken)
  }, [])

  const stores = [store]

  return (
    <StoreContext.Provider value={{ store, setStore, stores }}>
      {children}
    </StoreContext.Provider>
  )
}

export const useStore = () => useContext(StoreContext)
