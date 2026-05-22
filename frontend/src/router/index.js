import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import WatchlistView from '@/views/WatchlistView.vue'
import StockDetail from '@/views/StockDetail.vue'
import Settings from '@/views/Settings.vue'
import BuyReference from '@/views/BuyReference.vue'
import RealtimePrice from '@/views/RealtimePrice.vue'
import WatchlistStockList from '@/views/WatchlistStockList.vue'
import LimitUpStocks from '@/views/LimitUpStocks.vue'
import SectorList from '@/views/SectorList.vue'
import SectorLargeOrder from '@/views/SectorLargeOrder.vue'
import StockQuery from '@/views/StockQuery.vue'
import TradeCal from '@/views/TradeCal.vue'
import StockBasic from '@/views/StockBasic.vue'
import DailyData from '@/views/DailyData.vue'
import WeeklyData from '@/views/WeeklyData.vue'
import SyncTasks from '@/views/SyncTasks.vue'
import SnapshotManage from '@/views/SnapshotManageView.vue'
import SignalManage from '@/views/SignalManage.vue'
import StockCalculator from '@/views/StockCalculator.vue'
import MovingAverageSlope from '@/views/MovingAverageSlope.vue'
import TagManage from '@/views/TagManage.vue'
import WatchlistManage from '@/views/WatchlistManage.vue'
import SectorDetail from '@/views/SectorDetail.vue'
import IndustryDailyFlow from '@/views/IndustryDailyFlow.vue'
import IncrementalIndustry from '@/views/IncrementalIndustry.vue'
import HotIndustries from '@/views/HotIndustries.vue'
import SectorHeat from '@/views/SectorHeat.vue'
import IndustryStockMoneyflow from '@/views/IndustryStockMoneyflow.vue'
import StockFundAnalysis from '@/views/StockFundAnalysis.vue'
import ConceptSectors from '@/views/ConceptSectors.vue'
import ConceptDetail from '@/views/ConceptDetail.vue'
import BuyPointQuery from '@/views/BuyPointQuery.vue'
import StrategyStockPicker from '@/views/StrategyStockPicker.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/watchlist/:id',
    name: 'Watchlist',
    component: WatchlistView,
    props: true
  },
  {
    path: '/stock/:tsCode',
    name: 'StockDetail',
    component: StockDetail,
    props: true
  },
  {
    path: '/buy-reference',
    name: 'BuyReference',
    component: BuyReference
  },
  {
    path: '/realtime-price',
    name: 'RealtimePrice',
    component: RealtimePrice
  },
  {
    path: '/watchlist-stocks',
    name: 'WatchlistStockList',
    component: WatchlistStockList,
    meta: { title: '关注清单' }
  },
  {
    path: '/limit-up',
    name: 'LimitUpStocks',
    component: LimitUpStocks
  },
  {
    path: '/sectors',
    name: 'SectorList',
    component: SectorList
  },
  {
    path: '/sector/detail',
    name: 'SectorDetail',
    component: SectorDetail,
    meta: { title: '板块详情' }
  },
  {
    path: '/sector-large-orders',
    name: 'SectorLargeOrder',
    component: SectorLargeOrder,
    meta: { title: '板块大单' }
  },
  {
    path: '/stock-query',
    name: 'StockQuery',
    component: StockQuery
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  },
  {
    path: '/basic-data/trade-cal',
    name: 'TradeCal',
    component: TradeCal
  },
  {
    path: '/basic-data/stocks',
    name: 'StockBasic',
    component: StockBasic
  },
  {
    path: '/basic-data/daily',
    name: 'DailyData',
    component: DailyData
  },
  {
    path: '/basic-data/weekly',
    name: 'WeeklyData',
    component: WeeklyData
  },
  {
    path: '/sync-tasks',
    name: 'SyncTasks',
    component: SyncTasks
  },
  {
    path: '/snapshot-manage',
    name: 'SnapshotManage',
    component: SnapshotManage,
    meta: { title: '快照管理' }
  },
  {
    path: '/signal-manage',
    name: 'SignalManage',
    component: SignalManage,
    meta: { title: '信号管理' }
  },
  {
    path: '/stock-calculator',
    name: 'StockCalculator',
    component: StockCalculator,
    meta: { title: '股票计算器' }
  },
  {
    path: '/moving-average-slope',
    name: 'MovingAverageSlope',
    component: MovingAverageSlope,
    meta: { title: '均线斜率' }
  },
  {
    path: '/basic-data/tags',
    name: 'TagManage',
    component: TagManage,
    meta: { title: '标签管理' }
  },
  {
    path: '/basic-data/watchlists',
    name: 'WatchlistManage',
    component: WatchlistManage,
    meta: { title: '股票分组' }
  },


  {
    path: '/industry-daily-flow',
    name: 'IndustryDailyFlow',
    component: IndustryDailyFlow,
    meta: { title: '行业每日净流入' }
  },
  {
    path: '/incremental-industry',
    name: 'IncrementalIndustry',
    component: IncrementalIndustry,
    meta: { title: '增量行业' }
  },
  {
    path: '/hot-industries',
    name: 'HotIndustries',
    component: HotIndustries,
    meta: { title: '火热行业' }
  },
  {
    path: '/sector-heat',
    name: 'SectorHeat',
    component: SectorHeat,
    meta: { title: '板块热度' }
  },
  {
    path: '/industry-stock-moneyflow',
    name: 'IndustryStockMoneyflow',
    component: IndustryStockMoneyflow,
    meta: { title: '行业个股资金流' }
  },
  {
    path: '/stock-fund-analysis',
    name: 'StockFundAnalysis',
    component: StockFundAnalysis,
    meta: { title: '个股资金分析' }
  },
  {
    path: '/concept-sectors',
    name: 'ConceptSectors',
    component: ConceptSectors,
    meta: { title: '概念板块' }
  },
  {
    path: '/concept/detail',
    name: 'ConceptDetail',
    component: ConceptDetail,
    meta: { title: '板块明细' }
  },
  {
    path: '/buy-point-query',
    name: 'BuyPointQuery',
    component: BuyPointQuery,
    meta: { title: '买点查询' }
  },
  {
    path: '/strategy-stock-picker',
    name: 'StrategyStockPicker',
    component: StrategyStockPicker,
    meta: { title: '策略选股' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
