import { useQuery } from '@tanstack/react-query'
import * as api from '../api/client.js'
import { useStore } from '../context/StoreContext.jsx'

const opts = { staleTime: 5 * 60 * 1000, retry: 2 }

export const useSummary        = () => { const { store } = useStore(); return useQuery({ queryKey: ['summary', store.domain],         queryFn: () => api.fetchSummary(store.domain),                  ...opts }) }
export const useMonthlyRevenue = (months) => { const { store } = useStore(); return useQuery({ queryKey: ['revenue', store.domain, months],        queryFn: () => api.fetchMonthlyRevenue(store.domain, months),    ...opts }) }
export const useAOVTrend       = (period) => { const { store } = useStore(); return useQuery({ queryKey: ['aov', store.domain, period],             queryFn: () => api.fetchAOVTrend(store.domain, period),          ...opts }) }
export const useRepeatRate     = (months) => { const { store } = useStore(); return useQuery({ queryKey: ['repeatRate', store.domain, months],       queryFn: () => api.fetchRepeatRate(store.domain, months),        ...opts }) }
export const useAvgCLTV        = () => { const { store } = useStore(); return useQuery({ queryKey: ['avgCltv', store.domain],           queryFn: () => api.fetchAvgCLTV(store.domain),                   ...opts }) }
export const useTopCustomers   = (limit) => { const { store } = useStore(); return useQuery({ queryKey: ['topCustomers', store.domain, limit],      queryFn: () => api.fetchTopCustomers(store.domain, limit),       ...opts }) }
export const useCohortRetention= () => { const { store } = useStore(); return useQuery({ queryKey: ['cohorts', store.domain],           queryFn: () => api.fetchCohortRetention(store.domain),           ...opts }) }
export const useChurnSummary   = () => { const { store } = useStore(); return useQuery({ queryKey: ['churnSummary', store.domain],      queryFn: () => api.fetchChurnSummary(store.domain),              ...opts }) }
export const useChurnSignals   = (tier) => { const { store } = useStore(); return useQuery({ queryKey: ['churnSignals', store.domain, tier],       queryFn: () => api.fetchChurnSignals(store.domain, tier),        ...opts }) }
export const useTBODistribution= () => { const { store } = useStore(); return useQuery({ queryKey: ['tbo', store.domain],              queryFn: () => api.fetchTBODistribution(store.domain),           ...opts }) }
export const useProducts       = (limit) => { const { store } = useStore(); return useQuery({ queryKey: ['products', store.domain, limit],          queryFn: () => api.fetchProducts(store.domain, limit),           ...opts }) }
export const useShopInfo       = () => useQuery({ queryKey: ['shopInfo'], queryFn: () => api.fetchShopInfo(), staleTime: 10 * 60 * 1000, retry: 1 })
