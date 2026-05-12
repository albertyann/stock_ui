import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const longRunningApi = axios.create({
  baseURL: '/api/v1',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

longRunningApi.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('Long Running API Error:', error)
    return Promise.reject(error)
  }
)

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
  getAllWatchlistStocks: (params = {}) => {
    const { page = 1, page_size = 30, search = null, industry = null, watchlist_id = null, sort_by_change_pct = null, tags = [] } = params
    let url = `/watchlists/stocks/all?page=${page}&page_size=${page_size}`
    if (search) {
      url += `&search=${encodeURIComponent(search)}`
    }
    if (industry) {
      url += `&industry=${encodeURIComponent(industry)}`
    }
    if (watchlist_id) {
      url += `&watchlist_id=${watchlist_id}`
    }
    if (sort_by_change_pct) {
      url += `&sort_by_change_pct=${sort_by_change_pct}`
    }
    if (tags && tags.length > 0) {
      url += `&tags=${encodeURIComponent(tags.join(','))}`
    }
    return api.get(url)
  },
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
  updateStockNotes: (stockId, notes) =>
    api.put(`/watchlists/stocks/${stockId}/notes`, { notes }),
  // 获取所有标签
  getAllTags: () => api.get('/watchlists/tags'),
  // 更新股票标签
  updateStockTags: (tsCode, tags) =>
    api.put(`/watchlists/stocks/${tsCode}/tags`, { tags }),
  checkStocks: (tsCodes) => api.post('/watchlists/check-stocks', { ts_codes: tsCodes }),
  getStockByTsCode: (tsCode) => api.get(`/watchlists/stocks/by-ts-code/${tsCode}`),
  createSnapshot: (id, stocks) => api.post(`/watchlists/${id}/snapshots`, { stocks }),
  getSnapshots: (id) => api.get(`/watchlists/${id}/snapshots`),
  deleteSnapshot: (watchlistId, snapshotId) => api.delete(`/watchlists/${watchlistId}/snapshots/${snapshotId}`)
}

export const stockApi = {
  search: (q, limit = 20) => api.get(`/stocks/search?q=${q}&limit=${limit}`),
  getDetail: (tsCode) => api.get(`/stocks/${tsCode}`),
  getKline: (tsCode, period = 'daily', limit = 60) => 
    api.get(`/stocks/${tsCode}/kline?period=${period}&limit=${limit}`),
  getTags: (tsCode) => api.get(`/watchlists/stocks/${tsCode}/tags`),
  updateTags: (tsCode, tags) => api.put(`/watchlists/stocks/${tsCode}/tags`, { tags }),
  syncKline: (tsCode) => longRunningApi.post(`/stocks/${tsCode}/sync-kline`)
}

export const signalApi = {
  getAll: (params = {}) => api.get('/signals', { params }),
  getLatest: (tsCode) => api.get(`/signals/latest/${tsCode}`),
  analyze: (tsCodes) => api.post('/signals/analyze', { ts_codes: tsCodes }),
  analyzeAll: () => api.post('/signals/analyze-all'),
  addNote: (tsCode, noteContent) => api.post('/signals/note', { ts_code: tsCode, note_content: noteContent }),
  addTag: (tsCode, tags) => api.post('/signals/tag', { ts_code: tsCode, tags: tags }),
  // Signal management (paginated)
  getSignalsManage: (params = {}) => {
    const { page = 1, page_size = 20, ts_code = null, signal_type = null, is_active = null, signal_date = null, signal_date_start = null, signal_date_end = null } = params
    let url = `/signals/manage?page=${page}&page_size=${page_size}`
    if (ts_code) url += `&ts_code=${encodeURIComponent(ts_code)}`
    if (signal_type) url += `&signal_type=${encodeURIComponent(signal_type)}`
    if (is_active !== null && is_active !== undefined) url += `&is_active=${is_active}`
    if (signal_date) url += `&signal_date=${signal_date}`
    if (signal_date_start) url += `&signal_date_start=${signal_date_start}`
    if (signal_date_end) url += `&signal_date_end=${signal_date_end}`
    return api.get(url)
  },
  deleteSignal: (id) => api.delete(`/signals/${id}`),
  // 买点查询
  getBuyPoints: (params = {}) => {
    const { page = 1, page_size = 30, signal_date = null, signal_date_start = null, signal_date_end = null } = params
    let url = `/signals/manage?page=${page}&page_size=${page_size}&signal_type=ADD_TAG&note_content=买点`
    if (signal_date) url += `&signal_date=${signal_date}`
    if (signal_date_start) url += `&signal_date_start=${signal_date_start}`
    if (signal_date_end) url += `&signal_date_end=${signal_date_end}`
    return api.get(url)
  }
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
  // 按日期查询股票价格 (T, T+N)
  queryByDate: (tsCodes, queryDate, days = null) =>
    api.post('/realtime/query-by-date', { ts_codes: tsCodes, query_date: queryDate, days })
}

export const sectorApi = {
  getStockConcepts: (tsCode) => api.get(`/sectors/stock-concepts/${tsCode}`),
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
  },
  getSectorLargeOrders: (tradeDate) => api.get(`/sectors/large-orders?trade_date=${tradeDate}`),
  getConceptSectors: (tradeDate = null, sectorType = null) => {
    const params = new URLSearchParams()
    if (tradeDate) {
      params.append('trade_date', tradeDate)
    }
    if (sectorType) {
      params.append('sector_type', sectorType)
    }
    const queryString = params.toString()
    return api.get(`/sectors/concepts${queryString ? '?' + queryString : ''}`)
  },
  getConceptSectorDetail: (tsCode) => api.get(`/sectors/concepts/${tsCode}`),
  getConceptSectorStocks: (tsCode, page = 1, pageSize = 20, search = null, sort = 'default', trend = null, tradeDate = null) => {
    let url = `/sectors/concepts/${tsCode}/stocks?page=${page}&page_size=${pageSize}&sort=${sort}`
    if (search) {
      url += `&search=${encodeURIComponent(search)}`
    }
    if (trend) {
      url += `&trend=${trend}`
    }
    if (tradeDate) {
      url += `&trade_date=${tradeDate}`
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
  execute: (id, params = {}) => longRunningApi.post(`/sync-tasks/${id}/execute`, { params }),
  getLogs: (params = {}) => {
    const { task_name = null, page = 1, page_size = 10 } = params
    let url = `/sync-tasks/logs?page=${page}&page_size=${page_size}`
    if (task_name) url += `&task_name=${encodeURIComponent(task_name)}`
    return api.get(url)
  }
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
  getLastTradeDate: (exchange = 'SSE') => api.get(`/basic-data/trade-cal/last?exchange=${exchange}`),
  getStockBasic: (params = {}) => {
    const { page = 1, page_size = 20, name = null, ts_code = null, symbol = null, industry = null } = params
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
    if (industry) {
      url += `&industry=${encodeURIComponent(industry)}`
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
  },
  getStkWeeklyMonthly: (tsCode, freq = 'week', limit = 60) => {
    return api.get(`/basic-data/stk-weekly-monthly/${tsCode}?freq=${freq}&limit=${limit}`)
  },
  getMoneyflow: (tsCode, limit = 20) => {
    return api.get(`/basic-data/moneyflow/${tsCode}?limit=${limit}`)
  },
  getMoneyflowIndThs: (params = {}) => {
    const { page = 1, page_size = 20, industry = null, trade_date = null, ts_code = null, sort_field = null, sort_order = null } = params
    let url = `/basic-data/moneyflow-ind-ths?page=${page}&page_size=${page_size}`
    if (industry) {
      url += `&industry=${encodeURIComponent(industry)}`
    }
    if (trade_date) {
      url += `&trade_date=${trade_date}`
    }
    if (ts_code) {
      url += `&ts_code=${encodeURIComponent(ts_code)}`
    }
    if (sort_field) {
      url += `&sort_field=${encodeURIComponent(sort_field)}`
    }
    if (sort_order) {
      url += `&sort_order=${encodeURIComponent(sort_order)}`
    }
    return api.get(url)
  },
  getMoneyflowIndThsHistory: (tsCodes, days = 60) => {
    const codes = Array.isArray(tsCodes) ? tsCodes.join(',') : tsCodes
    return api.get(`/basic-data/moneyflow-ind-ths/history?ts_codes=${encodeURIComponent(codes)}&days=${days}`)
  },
  getMoneyflowIndThsIndustries: () => api.get('/basic-data/moneyflow-ind-ths/industries'),
  getCapitalFlow: (params = {}) => {
    const { days = 20, industry = null, ts_code = null, sort_field = null, sort_order = null } = params
    let url = `/basic-data/capital-flow?days=${days}`
    if (industry) {
      url += `&industry=${encodeURIComponent(industry)}`
    }
    if (ts_code) {
      url += `&ts_code=${encodeURIComponent(ts_code)}`
    }
    if (sort_field) {
      url += `&sort_field=${encodeURIComponent(sort_field)}`
    }
    if (sort_order) {
      url += `&sort_order=${encodeURIComponent(sort_order)}`
    }
    return api.get(url)
  },
  getIndustryDailyFlow: (params = {}) => {
    const { trade_date = null, days = 30, industry = null, sort_field = null, sort_order = null } = params
    let url = `/basic-data/industry-daily-flow?days=${days}`
    if (trade_date) {
      url += `&trade_date=${trade_date}`
    }
    if (industry) {
      url += `&industry=${encodeURIComponent(industry)}`
    }
    if (sort_field) {
      url += `&sort_field=${encodeURIComponent(sort_field)}`
    }
    if (sort_order) {
      url += `&sort_order=${encodeURIComponent(sort_order)}`
    }
    return api.get(url)
  },
  getIndustryStockMoneyflow: (params = {}) => {
    const { industry, trade_date = null, limit = 100 } = params
    let url = `/basic-data/industry-stock-moneyflow?industry=${encodeURIComponent(industry)}`
    if (trade_date) {
      url += `&trade_date=${trade_date}`
    }
    url += `&limit=${limit}`
    return api.get(url)
  },
  getIncrementalIndustry: (days = 20, min_growth_days = 3, end_date = null) => {
    let url = `/basic-data/incremental-industry?days=${days}&min_growth_days=${min_growth_days}`
    if (end_date) {
      url += `&end_date=${end_date}`
    }
    return api.get(url)
  },
  getHotIndustries: (params = {}) => {
    const { trade_date = null, min_amount = null, sort_field = null, sort_order = null } = params
    let url = `/basic-data/hot-industries`
    const queryParams = []
    if (trade_date) {
      queryParams.push(`trade_date=${encodeURIComponent(trade_date)}`)
    }
    if (min_amount !== null) {
      queryParams.push(`min_amount=${min_amount}`)
    }
    if (sort_field) {
      queryParams.push(`sort_field=${encodeURIComponent(sort_field)}`)
    }
    if (sort_order) {
      queryParams.push(`sort_order=${encodeURIComponent(sort_order)}`)
    }
    if (queryParams.length > 0) {
      url += `?${queryParams.join('&')}`
    }
    return api.get(url)
  },
  getStockCapitalFlow: (days = 30, limit = 20, end_date = null, ts_codes = null) => {
    let url = `/basic-data/stock-capital-flow?days=${days}&limit=${limit}`
    if (end_date) {
      url += `&end_date=${end_date}`
    }
    if (ts_codes && ts_codes.length > 0) {
      url += `&ts_codes=${encodeURIComponent(ts_codes.join(','))}`
    }
    return api.get(url)
  },
  getCyqChips: (tsCode, tradeDate = null) => {
    let url = `/basic-data/cyq-chips/${tsCode}`
    if (tradeDate) {
      url += `?trade_date=${tradeDate}`
    }
    return api.get(url)
  },
  getSectorHeat: (params = {}) => {
    const { trade_date = null, tab = 'up_pct', idx_type = null, min_stocks = null } = params
    let url = `/basic-data/sector-heat?tab=${tab}`
    if (trade_date) {
      url += `&trade_date=${encodeURIComponent(trade_date)}`
    }
    if (idx_type) {
      url += `&idx_type=${encodeURIComponent(idx_type)}`
    }
    if (min_stocks) {
      url += `&min_stocks=${min_stocks}`
    }
    return api.get(url)
  }
}

export const tagApi = {
  getAll: (params = {}) => {
    const { page = 1, page_size = 20, name = null } = params
    let url = `/tags?page=${page}&page_size=${page_size}`
    if (name) {
      url += `&name=${encodeURIComponent(name)}`
    }
    return api.get(url)
  },
  getAllTags: () => api.get('/tags/all'),
  get: (id) => api.get(`/tags/${id}`),
  create: (data) => api.post('/tags', data),
  update: (id, data) => api.put(`/tags/${id}`, data),
  delete: (id) => api.delete(`/tags/${id}`)
}

export const stockInfoApi = {
  get: (tsCode) => api.get(`/stock-info/${tsCode}`),
  create: (data) => api.post('/stock-info/', data),
  update: (id, data) => api.put(`/stock-info/${id}`, data),
  delete: (id) => api.delete(`/stock-info/${id}`)
}

export default api
