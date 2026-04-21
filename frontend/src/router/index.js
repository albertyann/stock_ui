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
import StockQuery from '@/views/StockQuery.vue'
import TradeCal from '@/views/TradeCal.vue'
import StockBasic from '@/views/StockBasic.vue'
import DailyData from '@/views/DailyData.vue'
import WeeklyData from '@/views/WeeklyData.vue'
import SyncTasks from '@/views/SyncTasks.vue'
import SnapshotManage from '@/views/SnapshotManageView.vue'
import SignalManage from '@/views/SignalManage.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
