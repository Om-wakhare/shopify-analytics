// Realistic mock data for a mid-sized D2C Shopify store
// All monetary values in USD

const now = new Date()
const monthsBack = (n) => {
  const d = new Date(now)
  d.setMonth(d.getMonth() - n)
  d.setDate(1)
  return d.toISOString()
}

// ── Summary KPIs ────────────────────────────────────────────────────────────
export const mockSummary = {
  store_id: 'f4a1b2c3-d4e5-6789-abcd-ef0123456789',
  total_orders: 8_412,
  total_customers: 5_230,
  total_revenue_usd: 624_850.40,
  aov_usd: 74.28,
  repeat_customers: 2_341,
  repeat_order_rate_pct: 44.76,
}

// ── Monthly Revenue (12 months) ─────────────────────────────────────────────
const baseRevenue = 38_000
export const mockMonthlyRevenue = Array.from({ length: 13 }, (_, i) => {
  const growth = 1 + i * 0.055
  const seasonal = 1 + Math.sin((i / 12) * Math.PI) * 0.15
  const revenue = Math.round(baseRevenue * growth * seasonal)
  const newPct = 0.48 - i * 0.01
  const newRev = Math.round(revenue * newPct)
  return {
    month: monthsBack(12 - i),
    order_count: Math.round(revenue / 72),
    unique_customers: Math.round(revenue / 95),
    revenue_usd: revenue,
    aov_usd: +(revenue / Math.round(revenue / 72)).toFixed(2),
    new_customers: Math.round(revenue / 95 * newPct),
    returning_customers: Math.round(revenue / 95 * (1 - newPct)),
  }
})

// ── AOV Trend ───────────────────────────────────────────────────────────────
export const mockAOVTrend = mockMonthlyRevenue.map((r) => ({
  period: r.month,
  aov_usd: r.aov_usd,
  order_count: r.order_count,
}))

// ── Repeat Order Rate ───────────────────────────────────────────────────────
export const mockRepeatRate = mockMonthlyRevenue.map((r, i) => ({
  month: r.month,
  new_customers: r.new_customers,
  repeat_customers: r.returning_customers,
  repeat_order_rate_pct: +((r.returning_customers / r.unique_customers) * 100).toFixed(2),
}))

// ── CLTV avg ────────────────────────────────────────────────────────────────
export const mockAvgCLTV = {
  customer_count: 5230,
  avg_historical_cltv: 119.47,
  avg_projected_12m_cltv: 168.32,
  avg_aov: 74.28,
  avg_tbo_days: 47.3,
}

// ── Top customers by CLTV ───────────────────────────────────────────────────
export const mockTopCustomers = Array.from({ length: 20 }, (_, i) => ({
  customer_id: `cust-${i + 1}`,
  historical_cltv_usd: +(980 - i * 38 + Math.random() * 20).toFixed(2),
  projected_12m_cltv_usd: +(1240 - i * 45 + Math.random() * 30).toFixed(2),
  total_orders: Math.max(2, 12 - i + Math.floor(Math.random() * 3)),
  aov_usd: +(65 + Math.random() * 40).toFixed(2),
  avg_days_between_orders: +(30 + Math.random() * 60).toFixed(1),
  days_since_last_order: Math.round(5 + Math.random() * 45),
  email: `customer${i + 1}@example.com`,
  cohort_month: monthsBack(18 - i),
}))

// ── Cohort Retention ────────────────────────────────────────────────────────
const cohortMonths = 12
const maxOffset = 11
export const mockCohortRetention = []
for (let c = 0; c < cohortMonths; c++) {
  const size = Math.round(180 + Math.random() * 120)
  for (let o = 0; o <= Math.min(maxOffset, cohortMonths - c - 1); o++) {
    const base = o === 0 ? 100 : Math.max(8, 58 * Math.exp(-o * 0.22) + (Math.random() - 0.5) * 6)
    mockCohortRetention.push({
      cohort_month: monthsBack(cohortMonths - c),
      cohort_size: size,
      month_offset: o,
      active_customers: Math.round((base / 100) * size),
      retention_rate_pct: +base.toFixed(1),
    })
  }
}

// ── Churn Summary ───────────────────────────────────────────────────────────
export const mockChurnSummary = [
  { churn_risk_tier: 'healthy',       customer_count: 2104, revenue_at_risk_usd: 0 },
  { churn_risk_tier: 'low_risk',      customer_count: 892,  revenue_at_risk_usd: 68_400 },
  { churn_risk_tier: 'medium_risk',   customer_count: 541,  revenue_at_risk_usd: 47_200 },
  { churn_risk_tier: 'high_risk',     customer_count: 318,  revenue_at_risk_usd: 38_750 },
  { churn_risk_tier: 'one_time_buyer',customer_count: 1375, revenue_at_risk_usd: 52_100 },
]

// ── Churn Signals (list) ────────────────────────────────────────────────────
const tiers = ['high_risk','high_risk','medium_risk','medium_risk','medium_risk','low_risk','low_risk','one_time_buyer']
export const mockChurnSignals = Array.from({ length: 40 }, (_, i) => ({
  customer_id: `at-risk-${i + 1}`,
  store_id: 'f4a1b2c3',
  days_since_last_order: Math.round(60 + Math.random() * 200),
  avg_days_between_orders: +(25 + Math.random() * 55).toFixed(1),
  historical_cltv_usd: +(80 + Math.random() * 400).toFixed(2),
  total_orders: Math.round(1 + Math.random() * 8),
  churn_risk_tier: tiers[i % tiers.length],
  last_order_at: monthsBack(Math.round(2 + Math.random() * 7)),
  email: `atrisk${i + 1}@example.com`,
}))

// ── TBO Distribution ────────────────────────────────────────────────────────
export const mockTBODistribution = [
  { bucket: '0-7d',     customer_count: 124, avg_tbo_in_bucket: 4.2 },
  { bucket: '8-14d',    customer_count: 287, avg_tbo_in_bucket: 11.1 },
  { bucket: '15-30d',   customer_count: 613, avg_tbo_in_bucket: 22.4 },
  { bucket: '31-60d',   customer_count: 891, avg_tbo_in_bucket: 44.8 },
  { bucket: '61-90d',   customer_count: 542, avg_tbo_in_bucket: 74.2 },
  { bucket: '91-180d',  customer_count: 318, avg_tbo_in_bucket: 128.6 },
  { bucket: '181-365d', customer_count: 127, avg_tbo_in_bucket: 243.1 },
  { bucket: '365d+',    customer_count: 42,  avg_tbo_in_bucket: 478.0 },
]

// ── Product Performance ─────────────────────────────────────────────────────
const products = [
  'Premium Bundle Kit','Signature Serum','Daily Essentials Set','Glow Face Mask',
  'Recovery Cream','Eye Contour Gel','Hydra Booster','SPF 50 Defense',
  'Night Repair Oil','Toner & Mist Duo',
]
export const mockProducts = products.map((title, i) => ({
  shopify_product_id: 1000 + i,
  product_title: title,
  vendor: ['Glow Co','Pure Lab','Revive Skin','NatureSkin'][i % 4],
  product_type: ['Bundle','Serum','Set','Treatment'][i % 4],
  order_count: Math.round(1800 - i * 160 + Math.random() * 80),
  units_sold:  Math.round(2200 - i * 190 + Math.random() * 100),
  revenue_usd: +(68000 - i * 5800 + Math.random() * 1200).toFixed(2),
  avg_unit_price: +(28 + i * 2.5 + Math.random() * 5).toFixed(2),
  unique_customers: Math.round(1400 - i * 120 + Math.random() * 60),
}))
