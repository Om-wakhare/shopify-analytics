import * as mock from './mockData.js'

// Set to false to hit the real FastAPI backend
const USE_MOCK = false
const BASE_URL = import.meta.env.VITE_API_URL || '/api'

function getToken() {
  return localStorage.getItem('shopify_analytics_token')
}

async function apiFetch(path) {
  const token = getToken()
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, { headers })
  if (res.status === 401) {
    // Token expired — redirect to login
    localStorage.removeItem('shopify_analytics_token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

function delay(ms = 400) {
  return new Promise((r) => setTimeout(r, ms))
}

// ── KPI API ─────────────────────────────────────────────────────────────────

export async function fetchSummary(shop) {
  if (USE_MOCK) { await delay(); return mock.mockSummary }
  return apiFetch(`/kpi/${shop}/summary`)
}

export async function fetchMonthlyRevenue(shop, months = 12) {
  if (USE_MOCK) { await delay(); return mock.mockMonthlyRevenue.slice(-months) }
  return apiFetch(`/kpi/${shop}/revenue?months=${months}`)
}

export async function fetchAOVTrend(shop, period = 'month') {
  if (USE_MOCK) { await delay(); return mock.mockAOVTrend }
  return apiFetch(`/kpi/${shop}/aov?period=${period}`)
}

export async function fetchRepeatRate(shop, months = 12) {
  if (USE_MOCK) { await delay(); return mock.mockRepeatRate.slice(-months) }
  return apiFetch(`/kpi/${shop}/repeat-rate?months=${months}`)
}

export async function fetchAvgCLTV(shop) {
  if (USE_MOCK) { await delay(); return mock.mockAvgCLTV }
  return apiFetch(`/kpi/${shop}/cltv/avg`)
}

export async function fetchTopCustomers(shop, limit = 20) {
  if (USE_MOCK) { await delay(); return mock.mockTopCustomers.slice(0, limit) }
  return apiFetch(`/kpi/${shop}/cltv?limit=${limit}`)
}

export async function fetchCohortRetention(shop, maxOffset = 11) {
  if (USE_MOCK) { await delay(); return mock.mockCohortRetention }
  return apiFetch(`/kpi/${shop}/cohorts?max_offset=${maxOffset}`)
}

export async function fetchChurnSummary(shop) {
  if (USE_MOCK) { await delay(); return mock.mockChurnSummary }
  return apiFetch(`/kpi/${shop}/churn/summary`)
}

export async function fetchChurnSignals(shop, tier = '') {
  if (USE_MOCK) {
    await delay()
    return tier ? mock.mockChurnSignals.filter(c => c.churn_risk_tier === tier) : mock.mockChurnSignals
  }
  return apiFetch(`/kpi/${shop}/churn${tier ? `?risk_tier=${tier}` : ''}`)
}

export async function fetchTBODistribution(shop) {
  if (USE_MOCK) { await delay(); return mock.mockTBODistribution }
  return apiFetch(`/kpi/${shop}/tbo`)
}

export async function fetchProducts(shop, limit = 10) {
  if (USE_MOCK) { await delay(); return mock.mockProducts.slice(0, limit) }
  return apiFetch(`/kpi/${shop}/products?limit=${limit}`)
}

export async function fetchShopInfo() {
  if (USE_MOCK) {
    await delay()
    return {
      shop_name: 'Glow Co Store', shop_owner_email: 'owner@glowco.com',
      shop_owner_name: 'Alex Johnson', shop_plan: 'Basic', currency: 'USD',
      timezone: 'America/New_York', primary_domain: 'https://glowco.com',
      subscription_status: 'trial', subscription_plan: null,
      trial_ends_at: new Date(Date.now() + 10 * 86400000).toISOString(),
      customers_synced: 87, orders_synced: 174, last_sync_at: new Date().toISOString(),
    }
  }
  return apiFetch('/shop/info')
}

export async function fetchSearch(query) {
  if (!query || !query.trim()) return { customers: [], products: [], orders: [] }
  if (USE_MOCK) {
    await delay(200)
    return {
      customers: [{ id: '1', email: `${query}@example.com`, total_spent: 249.99, orders_count: 3, type: 'customer' }],
      products:  [{ id: '100', title: `${query} Serum`, vendor: 'Glow Co', type: 'product' }],
      orders:    [],
    }
  }
  return apiFetch(`/search?q=${encodeURIComponent(query)}`)
}
