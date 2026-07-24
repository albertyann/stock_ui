<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card" @click="$router.push('/watchlist/2')" style="cursor: pointer;">
          <div class="stat-value">{{ kpdStocksCount }}</div>
          <div class="stat-label">开票盯股票</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ totalStocks }}</div>
          <div class="stat-label">关注股票数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card buy">
          <div class="stat-value">{{ buySignals }}</div>
          <div class="stat-label">买入信号</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card sell">
          <div class="stat-value">{{ sellSignals }}</div>
          <div class="stat-label">卖出信号</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card class="quick-access-card" @click="$router.push('/realtime-price')">
          <div class="quick-access-content">
            <el-icon class="quick-icon"><DataLine /></el-icon>
            <div class="quick-text">
              <div class="quick-title">实时股价</div>
              <div class="quick-desc">查看股票实时行情数据</div>
            </div>
            <el-button type="primary" size="small">
              立即查看 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>我的分组</span>
              <el-button type="primary" size="small" @click="$router.push('/settings')">
                设置
              </el-button>
            </div>
          </template>
          <el-table :data="watchlists" style="width: 100%">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="stock_count" label="数量" width="80" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="index-card-section">
          <template #header>
            <div class="card-header">
              <span>市场指数</span>
            </div>
          </template>
          <el-empty v-if="!indexData.length" description="暂无指数数据" />
          <div v-else class="index-grid">
            <div
              v-for="idx in indexData"
              :key="idx.ts_code"
              class="index-card"
              @click="$router.push('/index/' + idx.ts_code)"
            >
              <div class="index-name">{{ idx.name || idx.ts_code }}</div>
              <div class="index-price" :class="idx.change_pct >= 0 ? 'up' : 'down'">
                {{ formatPrice(idx.close) }}
              </div>
              <div class="index-change" :class="idx.change_pct >= 0 ? 'up' : 'down'">
                {{ idx.change_pct >= 0 ? '+' : '' }}{{ idx.change_pct?.toFixed(2) }}%
              </div>
              <div class="index-meta">
                <span>高 {{ formatPrice(idx.high) }}</span>
                <span>低 {{ formatPrice(idx.low) }}</span>
              </div>
              <div class="index-date">{{ idx.date }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { signalApi, watchlistApi, basicDataApi } from '@/api'
import { storeToRefs } from 'pinia'

const store = useWatchlistStore()
const { watchlists } = storeToRefs(store)

const totalStocks = ref(0)
const buySignals = ref(0)
const sellSignals = ref(0)
const indexData = ref([])

// 计算开票盯股票（watchlist id=2）的股票数量
const kpdStocksCount = computed(() => {
  const kpdWatchlist = watchlists.value.find(w => w.id === 2)
  return kpdWatchlist?.stock_count || kpdWatchlist?.stocks?.length || 0
})

onMounted(async () => {
  await store.fetchWatchlists()
  await fetchDashboardData()
})

const fetchDashboardData = async () => {
  try {
    // 获取指数概览
    const indexRes = await basicDataApi.getIndexDailyOverview()
    indexData.value = indexRes.data || []

    // 获取信号统计数据
    const signalRes = await signalApi.getAll({ limit: 10 })
    const signals = signalRes.data || []
    buySignals.value = signals.filter(s => s.signal_type === 'BUY').length
    sellSignals.value = signals.filter(s => s.signal_type === 'SELL').length

    // 获取统计信息 (status=1 的热点股票数)
    const statsResponse = await watchlistApi.getStats()
    if (statsResponse.data) {
      totalStocks.value = statsResponse.data.hot_stocks || 0
    }
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

const formatPrice = (val) => {
  if (val === null || val === undefined) return '--'
  return val.toFixed(2)
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
  background: var(--bg-card-solid);
  border: 1px solid var(--border-subtle);
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: var(--accent);
}

.stat-card.buy .stat-value {
  color: var(--stock-up);
}

.stat-card.sell .stat-value {
  color: var(--stock-down);
}

.stat-label {
  margin-top: 10px;
  color: var(--text-muted);
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.index-card-section :deep(.el-card__body) {
  padding: 12px;
}

.index-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.index-card {
  background: var(--bg-card-solid);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.index-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border-color: var(--border-active);
}

.index-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.index-price {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 4px;
}

.index-price.up,
.index-change.up {
  color: var(--stock-up);
}

.index-price.down,
.index-change.down {
  color: var(--stock-down);
}

.index-change {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.index-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
}

.index-date {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 6px;
  opacity: 0.6;
}

.quick-access-card {
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.12) 100%);
  border: 1px solid var(--border-active);
}

.quick-access-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2);
}

.quick-access-card :deep(.el-card__body) {
  padding: 20px;
}

.quick-access-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-primary);
}

.quick-icon {
  font-size: 48px;
  margin-right: 16px;
  opacity: 0.9;
  color: var(--accent);
}

.quick-text {
  flex: 1;
}

.quick-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 4px;
}

.quick-desc {
  font-size: 14px;
  opacity: 0.7;
  color: var(--text-secondary);
}
</style>
