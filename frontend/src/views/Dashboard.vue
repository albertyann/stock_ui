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
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最新信号</span>
            </div>
          </template>
          <el-empty v-if="!recentSignals.length" description="暂无信号" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="signal in recentSignals"
              :key="signal.id"
              :type="signalType(signal.signal_type)"
            >
              <div class="signal-item">
                <div class="signal-header">
                  <span class="stock-name">{{ signal.ts_code }}</span>
                  <el-tag :type="signalType(signal.signal_type)" size="small">
                    {{ signalText(signal.signal_type) }}
                  </el-tag>
                </div>
                <div class="signal-info">
                  强度: {{ signal.signal_strength }}/5 | 
                  日期: {{ formatDate(signal.signal_date) }}
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { signalApi, watchlistApi } from '@/api'
import { storeToRefs } from 'pinia'

const store = useWatchlistStore()
const { watchlists } = storeToRefs(store)

const totalStocks = ref(0)
const buySignals = ref(0)
const sellSignals = ref(0)
const recentSignals = ref([])

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
    // 获取信号数据
    const response = await signalApi.getAll({ limit: 10 })
    recentSignals.value = response.data || []

    buySignals.value = recentSignals.value.filter(s => s.signal_type === 'BUY').length
    sellSignals.value = recentSignals.value.filter(s => s.signal_type === 'SELL').length

    // 获取统计信息 (status=1 的热点股票数)
    const statsResponse = await watchlistApi.getStats()
    if (statsResponse.data) {
      totalStocks.value = statsResponse.data.hot_stocks || 0
    }
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

const signalType = (type) => {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'info', NOTE: 'warning' }
  return map[type] || 'info'
}

const signalText = (type) => {
  const map = { BUY: '买入', SELL: '卖出', WATCH: '观望', NOTE: '备注' }
  return map[type] || type
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409EFF;
}

.stat-card.buy .stat-value {
  color: #67C23A;
}

.stat-card.sell .stat-value {
  color: #F56C6C;
}

.stat-label {
  margin-top: 10px;
  color: #606266;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.signal-item {
  padding: 10px 0;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.stock-name {
  font-weight: bold;
}

.signal-info {
  font-size: 12px;
  color: #909399;
}

.quick-access-card {
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.quick-access-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.quick-access-card :deep(.el-card__body) {
  padding: 20px;
}

.quick-access-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: white;
}

.quick-icon {
  font-size: 48px;
  margin-right: 16px;
  opacity: 0.9;
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
  opacity: 0.8;
}
</style>
