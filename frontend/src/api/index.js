import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const watchlistApi = {
  getAll: () => api.get('/watchlists'),
  create: (data) => api.post('/watchlists', data),
  get: (id) => api.get(`/watchlists/${id}`),
  update: (id, data) => api.put(`/watchlists/${id}`, data),
  delete: (id) => api.delete(`/watchlists/${id}`),
  getStocks: (id, signalDate = null) => {
    const params = signalDate ? `?signal_date=${signalDate}` : ''
    return api.get(`/watchlists/${id}/stocks${params}`)
  },
  addStock: (id, data) => api.post(`/watchlists/${id}/stocks`, data),
  removeStock: (id, stockId) => api.delete(`/watchlists/${id}/stocks/${stockId}`),
  batchAdd: (id, data) => api.post(`/watchlists/${id}/stocks/batch`, data),
  getAvailableDates: (id) => api.get(`/watchlists/${id}/dates`),
  getLastTradingDay: (watchlistId, exchange = 'SSE') => api.get(`/watchlists/${watchlistId}/last-trading-day?exchange=${exchange}`),
  getWatchReasons: (id) => api.get(`/watchlists/${id}/watch-reasons`),
  getWatchDates: (id) => api.get(`/watchlists/${id}/watch-dates`),
  updateStockStatus: (watchlistId, stockId, status) => 
    api.put(`/watchlists/${watchlistId}/stocks/${stockId}/status?status=${status}`),
  getStocksByWatchDate: (id, watchDate, limit = null) => {
    const params = new URLSearchParams()
    if (watchDate) {
      params.append('watch_date', watchDate)
    }
    if (limit) {
      params.append('limit', limit.toString())
    }
    const queryString = params.toString()
    const url = queryString ? `/watchlists/${id}/stocks?${queryString}` : `/watchlists/${id}/stocks`
    return api.get(url)
  },
  // 移动股票到另一个分组
  moveStockToWatchlist: (stockId, targetWatchlistId, reason) => 
    api.put(`/watchlists/stocks/${stockId}/move`, { 
      target_watchlist_id: targetWatchlistId,
      reason: reason 
    })
}

export const stockApi = {
  search: (q, limit = 20) => api.get(`/stocks/search?q=${q}&limit=${limit}`),
  getDetail: (tsCode) => api.get(`/stocks/${tsCode}`),
  getKline: (tsCode, period = 'daily', limit = 60) => 
    api.get(`/stocks/${tsCode}/kline?period=${period}&limit=${limit}`)
}

export const signalApi = {
  getAll: (params = {}) => api.get('/signals', { params }),
  getLatest: (tsCode) => api.get(`/signals/latest/${tsCode}`),
  analyze: (tsCodes) => api.post('/signals/analyze', { ts_codes: tsCodes }),
  analyzeAll: () => api.post('/signals/analyze-all')
}

export const realtimeApi = {
  getPrices: (tsCodes) => api.post('/realtime/prices', { ts_codes: tsCodes }),
  refresh: (tsCodes) => api.post('/realtime/refresh', { ts_codes: tsCodes }),
  healthCheck: () => api.get('/realtime/health'),
  // 获取指定股票池的价格
  getWatchlistPrices: (watchlistId, includeKline = false) =>
    api.get(`/realtime/watchlist/${watchlistId}?include_kline=${includeKline}`),
  // 获取所有股票池的价格
  getAllWatchlistsPrices: (includeKline = false) =>
    api.get(`/realtime/watchlists?include_kline=${includeKline}`),
  // 获取单只股票的K线
  getKline: (tsCode, period = 'daily', limit = 60) =>
    api.get(`/realtime/${tsCode}/kline?period=${period}&limit=${limit}`),
  // 批量获取K线
  getBatchKline: (tsCodes, period = 'daily', limit = 60) =>
    api.post(`/realtime/batch/kline?period=${period}&limit=${limit}`, tsCodes),
  // 获取涨停股票
  getLimitUpStocks: (params = {}) => {
    const { minChangePct = 9.9, limit = 200, tradeDate = null, industry = null } = params
    let url = `/realtime/limit-up?min_change_pct=${minChangePct}&limit=${limit}`
    if (tradeDate) {
      url += `&trade_date=${tradeDate}`
    }
    if (industry) {
      url += `&industry=${encodeURIComponent(industry)}`
    }
    return api.get(url)
  },
  // 获取股东人数数据
  getHolderNumber: (tsCode, limit = 60) =>
    api.get(`/realtime/${tsCode}/holder-number?limit=${limit}`),
  // 按日期查询股票价格 (T, T+1, T+3, T+7)
  queryByDate: (tsCodes, queryDate) =>
    api.post('/realtime/query-by-date', { ts_codes: tsCodes, query_date: queryDate })
}

export const sectorApi = {
  // 获取所有板块列表（行业）
  getAllSectors: () => api.get('/sectors'),
  // 获取板块详情
  getSectorDetail: (sectorCode, sectorType = 'industry') => 
    api.get(`/sectors/${sectorCode}?sector_type=${sectorType}`),
  // 获取板块内的股票列表
  getSectorStocks: (sectorCode, sectorType = 'industry', page = 1, pageSize = 20, search = null) => {
    let url = `/sectors/${sectorCode}/stocks?sector_type=${sectorType}&page=${page}&page_size=${pageSize}`
    if (search) {
      url += `&search=${encodeURIComponent(search)}`
    }
    return api.get(url)
  }
}

export default api
