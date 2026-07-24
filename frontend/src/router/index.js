import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '@/views/Dashboard.vue'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true, title: '登录' }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/realtime-price',
    name: 'RealtimePrice',
    component: () => import('@/views/RealtimePrice.vue')
  },
  {
    path: '/watchlist/:id',
    name: 'Watchlist',
    component: () => import('@/views/WatchlistView.vue'),
    props: true,
    meta: { requiresAdmin: true }
  },
  {
    path: '/stock/:tsCode',
    name: 'StockDetail',
    component: () => import('@/views/StockDetail.vue'),
    props: true,
    meta: { requiresAdmin: true }
  },
  {
    path: '/etf/:tsCode',
    name: 'EtfDetail',
    component: () => import('@/views/EtfDetail.vue'),
    props: true,
    meta: { title: 'ETF详情', requiresAdmin: true }
  },
  {
    path: '/watchlist-stocks',
    name: 'WatchlistStockList',
    component: () => import('@/views/WatchlistStockList.vue'),
    meta: { title: '关注清单', requiresAdmin: true }
  },
  {
    path: '/limit-up',
    name: 'LimitUpStocks',
    component: () => import('@/views/LimitUpStocks.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/sectors',
    name: 'SectorList',
    component: () => import('@/views/SectorList.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/sector/detail',
    name: 'SectorDetail',
    component: () => import('@/views/SectorDetail.vue'),
    meta: { title: '板块详情', requiresAdmin: true }
  },
  {
    path: '/stock-query',
    name: 'StockQuery',
    component: () => import('@/views/StockQuery.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/basic-data/trade-cal',
    name: 'TradeCal',
    component: () => import('@/views/TradeCal.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/basic-data/stocks',
    name: 'StockBasic',
    component: () => import('@/views/StockBasic.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/basic-data/etfs',
    name: 'EtfBasic',
    component: () => import('@/views/EtfBasic.vue'),
    meta: { title: 'ETF管理', requiresAdmin: true }
  },
  {
    path: '/basic-data/funds',
    name: 'FundBasic',
    component: () => import('@/views/FundBasic.vue'),
    meta: { title: '基金管理', requiresAdmin: true }
  },
  {
    path: '/fund/:tsCode',
    name: 'FundDetail',
    component: () => import('@/views/FundDetail.vue'),
    props: true,
    meta: { title: '基金详情', requiresAdmin: true }
  },
  {
    path: '/basic-data/index-basic',
    name: 'IndexBasic',
    component: () => import('@/views/IndexBasic.vue'),
    meta: { title: '指数管理', requiresAdmin: true }
  },
  {
    path: '/index/:tsCode',
    name: 'IndexDetail',
    component: () => import('@/views/IndexDetail.vue'),
    props: true,
    meta: { title: '指数详情', requiresAdmin: true }
  },
  {
    path: '/basic-data/daily',
    name: 'DailyData',
    component: () => import('@/views/DailyData.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/basic-data/weekly',
    name: 'WeeklyData',
    component: () => import('@/views/WeeklyData.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/sync-tasks',
    name: 'SyncTasks',
    component: () => import('@/views/SyncTasks.vue'),
    meta: { title: '数据同步', requiresAdmin: true }
  },
  {
    path: '/etf-sync',
    name: 'EtfSync',
    component: () => import('@/views/EtfSync.vue'),
    meta: { title: 'ETF同步', requiresAdmin: true }
  },
  {
    path: '/index-sync',
    name: 'IndexSync',
    component: () => import('@/views/IndexSync.vue'),
    meta: { title: '指数同步', requiresAdmin: true }
  },
  {
    path: '/snapshot-manage',
    name: 'SnapshotManage',
    component: () => import('@/views/SnapshotManageView.vue'),
    meta: { title: '快照管理', requiresAdmin: true }
  },
  {
    path: '/signal-manage',
    name: 'SignalManage',
    component: () => import('@/views/SignalManage.vue'),
    meta: { title: '信号管理', requiresAdmin: true }
  },
  {
    path: '/stock-calculator',
    name: 'StockCalculator',
    component: () => import('@/views/StockCalculator.vue'),
    meta: { title: '股票计算器', requiresAdmin: true }
  },
  {
    path: '/moving-average-slope',
    name: 'MovingAverageSlope',
    component: () => import('@/views/MovingAverageSlope.vue'),
    meta: { title: '均线斜率', requiresAdmin: true }
  },
  {
    path: '/indicator-calc',
    name: 'IndicatorCalc',
    component: () => import('@/views/IndicatorCalc.vue'),
    meta: { title: '指标计算', requiresAdmin: true }
  },
  {
    path: '/basic-data/tags',
    name: 'TagManage',
    component: () => import('@/views/TagManage.vue'),
    meta: { title: '标签管理', requiresAdmin: true }
  },
  {
    path: '/basic-data/watchlists',
    name: 'WatchlistManage',
    component: () => import('@/views/WatchlistManage.vue'),
    meta: { title: '股票分组', requiresAdmin: true }
  },
  {
    path: '/industry-daily-flow',
    name: 'IndustryDailyFlow',
    component: () => import('@/views/IndustryDailyFlow.vue'),
    meta: { title: '行业每日净流入', requiresAdmin: true }
  },
  {
    path: '/incremental-industry',
    name: 'IncrementalIndustry',
    component: () => import('@/views/IncrementalIndustry.vue'),
    meta: { title: '增量行业', requiresAdmin: true }
  },
  {
    path: '/hot-industries',
    name: 'HotIndustries',
    component: () => import('@/views/HotIndustries.vue'),
    meta: { title: '火热行业', requiresAdmin: true }
  },
  {
    path: '/sector-heat',
    name: 'SectorHeat',
    component: () => import('@/views/SectorHeat.vue'),
    meta: { title: '板块热度', requiresAdmin: true }
  },
  {
    path: '/industry-stock-moneyflow',
    name: 'IndustryStockMoneyflow',
    component: () => import('@/views/IndustryStockMoneyflow.vue'),
    meta: { title: '行业个股资金流', requiresAdmin: true }
  },
  {
    path: '/stock-fund-analysis',
    name: 'StockFundAnalysis',
    component: () => import('@/views/StockFundAnalysis.vue'),
    meta: { title: '个股资金分析', requiresAdmin: true }
  },
  {
    path: '/concept-sectors',
    name: 'ConceptSectors',
    component: () => import('@/views/ConceptSectors.vue'),
    meta: { title: '概念板块', requiresAdmin: true }
  },
  {
    path: '/concept/detail',
    name: 'ConceptDetail',
    component: () => import('@/views/ConceptDetail.vue'),
    meta: { title: '板块明细', requiresAdmin: true }
  },
  {
    path: '/buy-point-query',
    name: 'BuyPointQuery',
    component: () => import('@/views/BuyPointQuery.vue'),
    meta: { title: '买点查询', requiresAdmin: true }
  },
  {
    path: '/daily-scores',
    name: 'DailyScoreView',
    component: () => import('@/views/DailyScoreView.vue'),
    meta: { title: '每日量化评分', requiresAdmin: true }
  },
  {
    path: '/trading-heat',
    name: 'TradingHeat',
    component: () => import('@/views/TradingHeat.vue'),
    meta: { title: '交易热度', requiresAdmin: true }
  },
  {
    path: '/watchlist-sector-stats',
    name: 'WatchlistSectorStats',
    component: () => import('@/views/WatchlistSectorStats.vue'),
    meta: { title: '关注板块', requiresAdmin: true }
  },
  {
    path: '/watchlist-sector-trend',
    name: 'WatchlistSectorTrend',
    component: () => import('@/views/WatchlistSectorTrend.vue'),
    meta: { title: '板块趋势', requiresAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'AdminUserManage',
    component: () => import('@/views/admin/UserManage.vue'),
    meta: { title: '用户管理', requiresAdmin: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.initialized) {
    await authStore.init()
  }

  if (to.meta.public) {
    if (to.path === '/login' && authStore.isAuthenticated) {
      return '/'
    }
    return true
  }

  if (!authStore.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return '/'
  }

  return true
})

router.afterEach((to) => {
  const base = '小麦国度'
  document.title = to.meta?.title ? `${to.meta.title} - ${base}` : base
})

export default router
