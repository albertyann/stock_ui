import { createRouter, createWebHistory } from 'vue-router'

// 懒加载：所有视图按需打包，大幅减小首屏 chunk
// 仅 Dashboard 作为首页保持静态导入（用户落地页，避免首次跳转闪烁）
import Dashboard from '@/views/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/watchlist/:id',
    name: 'Watchlist',
    component: () => import('@/views/WatchlistView.vue'),
    props: true
  },
  {
    path: '/stock/:tsCode',
    name: 'StockDetail',
    component: () => import('@/views/StockDetail.vue'),
    props: true
  },
  {
    path: '/buy-reference',
    name: 'BuyReference',
    component: () => import('@/views/BuyReference.vue')
  },
  {
    path: '/realtime-price',
    name: 'RealtimePrice',
    component: () => import('@/views/RealtimePrice.vue')
  },
  {
    path: '/watchlist-stocks',
    name: 'WatchlistStockList',
    component: () => import('@/views/WatchlistStockList.vue'),
    meta: { title: '关注清单' }
  },
  {
    path: '/limit-up',
    name: 'LimitUpStocks',
    component: () => import('@/views/LimitUpStocks.vue')
  },
  {
    path: '/sectors',
    name: 'SectorList',
    component: () => import('@/views/SectorList.vue')
  },
  {
    path: '/sector/detail',
    name: 'SectorDetail',
    component: () => import('@/views/SectorDetail.vue'),
    meta: { title: '板块详情' }
  },
  {
    path: '/sector-large-orders',
    name: 'SectorLargeOrder',
    component: () => import('@/views/SectorLargeOrder.vue'),
    meta: { title: '板块大单' }
  },
  {
    path: '/stock-query',
    name: 'StockQuery',
    component: () => import('@/views/StockQuery.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  },
  {
    path: '/basic-data/trade-cal',
    name: 'TradeCal',
    component: () => import('@/views/TradeCal.vue')
  },
  {
    path: '/basic-data/stocks',
    name: 'StockBasic',
    component: () => import('@/views/StockBasic.vue')
  },
  {
    path: '/basic-data/daily',
    name: 'DailyData',
    component: () => import('@/views/DailyData.vue')
  },
  {
    path: '/basic-data/weekly',
    name: 'WeeklyData',
    component: () => import('@/views/WeeklyData.vue')
  },
  {
    path: '/sync-tasks',
    name: 'SyncTasks',
    component: () => import('@/views/SyncTasks.vue')
  },
  {
    path: '/snapshot-manage',
    name: 'SnapshotManage',
    component: () => import('@/views/SnapshotManageView.vue'),
    meta: { title: '快照管理' }
  },
  {
    path: '/signal-manage',
    name: 'SignalManage',
    component: () => import('@/views/SignalManage.vue'),
    meta: { title: '信号管理' }
  },
  {
    path: '/stock-calculator',
    name: 'StockCalculator',
    component: () => import('@/views/StockCalculator.vue'),
    meta: { title: '股票计算器' }
  },
  {
    path: '/moving-average-slope',
    name: 'MovingAverageSlope',
    component: () => import('@/views/MovingAverageSlope.vue'),
    meta: { title: '均线斜率' }
  },
  {
    path: '/basic-data/tags',
    name: 'TagManage',
    component: () => import('@/views/TagManage.vue'),
    meta: { title: '标签管理' }
  },
  {
    path: '/basic-data/watchlists',
    name: 'WatchlistManage',
    component: () => import('@/views/WatchlistManage.vue'),
    meta: { title: '股票分组' }
  },
  {
    path: '/industry-daily-flow',
    name: 'IndustryDailyFlow',
    component: () => import('@/views/IndustryDailyFlow.vue'),
    meta: { title: '行业每日净流入' }
  },
  {
    path: '/incremental-industry',
    name: 'IncrementalIndustry',
    component: () => import('@/views/IncrementalIndustry.vue'),
    meta: { title: '增量行业' }
  },
  {
    path: '/hot-industries',
    name: 'HotIndustries',
    component: () => import('@/views/HotIndustries.vue'),
    meta: { title: '火热行业' }
  },
  {
    path: '/sector-heat',
    name: 'SectorHeat',
    component: () => import('@/views/SectorHeat.vue'),
    meta: { title: '板块热度' }
  },
  {
    path: '/industry-stock-moneyflow',
    name: 'IndustryStockMoneyflow',
    component: () => import('@/views/IndustryStockMoneyflow.vue'),
    meta: { title: '行业个股资金流' }
  },
  {
    path: '/stock-fund-analysis',
    name: 'StockFundAnalysis',
    component: () => import('@/views/StockFundAnalysis.vue'),
    meta: { title: '个股资金分析' }
  },
  {
    path: '/concept-sectors',
    name: 'ConceptSectors',
    component: () => import('@/views/ConceptSectors.vue'),
    meta: { title: '概念板块' }
  },
  {
    path: '/concept/detail',
    name: 'ConceptDetail',
    component: () => import('@/views/ConceptDetail.vue'),
    meta: { title: '板块明细' }
  },
  {
    path: '/buy-point-query',
    name: 'BuyPointQuery',
    component: () => import('@/views/BuyPointQuery.vue'),
    meta: { title: '买点查询' }
  },
  {
    path: '/strategy-stock-picker',
    name: 'StrategyStockPicker',
    component: () => import('@/views/StrategyStockPicker.vue'),
    meta: { title: '策略选股' }
  },
  {
    path: '/daily-scores',
    name: 'DailyScoreView',
    component: () => import('@/views/DailyScoreView.vue'),
    meta: { title: '每日量化评分' }
  },
  {
    path: '/watchlist-sector-stats',
    name: 'WatchlistSectorStats',
    component: () => import('@/views/WatchlistSectorStats.vue'),
    meta: { title: '关注板块' }
  },
  {
    path: '/watchlist-sector-trend',
    name: 'WatchlistSectorTrend',
    component: () => import('@/views/WatchlistSectorTrend.vue'),
    meta: { title: '板块趋势' }
  },
  {
    // 404 兜底：重定向到首页
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

// 根据 meta.title 动态设置文档标题
router.afterEach((to) => {
  const base = '小麦国度'
  document.title = to.meta?.title ? `${to.meta.title} - ${base}` : base
})

export default router
