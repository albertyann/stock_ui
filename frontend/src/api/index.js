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
  getStats: () => api.get('/watchlists/stats/overview'),
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
    }),
  // 更新股票备注
  updateStockNotes: (watchlistId, stockId, notes) =>
    api.put(`/watchlists/${watchlistId}/stocks/${stockId}/notes`, { notes }),
  checkStocks: (tsCodes) => api.post('/watchlists/check-stocks', { ts_codes: tsCodes }),
  createSnapshot: (id, stocks) => api.post(`/watchlists/${id}/snapshots`, { stocks }),
  getSnapshots: (id) => api.get(`/watchlists/${id}/snapshots`),
  deleteSnapshot: (watchlistId, snapshotId) => api.delete(`/watchlists/${watchlistId}/snapshots/${snapshotId}`)
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

export const syncTaskApi = {
  getAll: () => api.get('/sync-tasks'),
  create: (data) => api.post('/sync-tasks', data),
  get: (id) => api.get(`/sync-tasks/${id}`),
  update: (id, data) => api.put(`/sync-tasks/${id}`, data),
  delete: (id) => api.delete(`/sync-tasks/${id}`),
  execute: (id, params = {}) => api.post(`/sync-tasks/${id}/execute`, { params })
}

export const basicDataApi = {
  getTradeCal: (params = {}) => {
    const { page = 1, page_size = 20, exchange = null, cal_date = null } = params
    let url = `/basic-data/trade-cal?page=${page}&page_size=${page_size}`
    if (exchange) {
      url += `&exchange=${encodeURIComponent(exchange)}`
    }
    if (cal_date) {
      url += `&cal_date=${cal_date}`
    }
    return api.get(url)
  },
  getExchanges: () => api.get('/basic-data/trade-cal/exchanges'),
  getStockBasic: (params = {}) => {
    const { page = 1, page_size = 20, name = null, ts_code = null, symbol = null } = params
    let url = `/basic-data/stocks?page=${page}&page_size=${page_size}`
    if (name) {
      url += `&name=${encodeURIComponent(name)}`
    }
    if (ts_code) {
      url += `&ts_code=${encodeURIComponent(ts_code)}`
    }
    if (symbol) {
      url += `&symbol=${encodeURIComponent(symbol)}`
    }
    return api.get(url)
  },
  getDailyData: (params = {}) => {
    const { page = 1, page_size = 20, name = null, ts_code = null, trade_date = null } = params
    let url = `/basic-data/daily?page=${page}&page_size=${page_size}`
    if (name) {
      url += `&name=${encodeURIComponent(name)}`
    }
    if (ts_code) {
      url += `&ts_code=${encodeURIComponent(ts_code)}`
    }
    if (trade_date) {
      url += `&trade_date=${trade_date}`
    }
    return api.get(url)
  },
  getWeeklyData: (params = {}) => {
    const { page = 1, page_size = 20, name = null, ts_code = null, trade_date = null } = params
    let url = `/basic-data/weekly?page=${page}&page_size=${page_size}`
    if (name) {
      url += `&name=${encodeURIComponent(name)}`
    }
    if (ts_code) {
      url += `&ts_code=${encodeURIComponent(ts_code)}`
    }
    if (trade_date) {
      url += `&trade_date=${trade_date}`
    }
    return api.get(url)
  }
}

export default api
