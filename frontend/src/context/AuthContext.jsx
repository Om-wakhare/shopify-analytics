import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

const TOKEN_KEY = 'shopify_analytics_token'

function parseJWT(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return null
  }
}

function isTokenExpired(payload) {
  if (!payload?.exp) return false
  return Date.now() / 1000 > payload.exp
}

export function AuthProvider({ children }) {
  const [token, setToken]   = useState(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser]     = useState(() => {
    const t = localStorage.getItem(TOKEN_KEY)
    return t ? parseJWT(t) : null
  })

  const login = useCallback((newToken) => {
    localStorage.setItem(TOKEN_KEY, newToken)
    setToken(newToken)
    setUser(parseJWT(newToken))
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [])

  // Auto-logout on token expiry
  useEffect(() => {
    if (token && isTokenExpired(parseJWT(token))) {
      logout()
    }
  }, [token, logout])

  const isAuthenticated = !!token && !!user && !isTokenExpired(user)
  const isSubscribed    = isAuthenticated && (
    user?.subscription_status === 'active' || user?.subscription_status === 'trial'
  )
  const isTrialExpired  = isAuthenticated &&
    user?.subscription_status === 'trial' &&
    user?.trial_ends_at &&
    new Date(user.trial_ends_at) < new Date()

  return (
    <AuthContext.Provider value={{
      token, user, login, logout,
      isAuthenticated, isSubscribed, isTrialExpired,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
