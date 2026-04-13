import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import WatchlistView from '@/views/WatchlistView.vue'
import StockDetail from '@/views/StockDetail.vue'
import Settings from '@/views/Settings.vue'
import BuyReference from '@/views/BuyReference.vue'
import RealtimePrice from '@/views/RealtimePrice.vue'
import LimitUpStocks from '@/views/LimitUpStocks.vue'
import SectorList from '@/views/SectorList.vue'
import StockQuery from '@/views/StockQuery.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
