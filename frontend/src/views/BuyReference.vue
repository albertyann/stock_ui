<template>
  <div class="buy-reference-page">
    <div class="page-header">
      <h2>买入参考</h2>
      <div class="header-actions">
        <el-button type="primary" @click="refresh" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">买入信号</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card">
          <div class="stat-value active">{{ stats.active }}</div>
          <div class="stat-label">待执行</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card">
          <div class="stat-value watching">{{ stats.watching }}</div>
          <div class="stat-label">观察中</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 过滤器 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <div class="filter-item">
          <span class="filter-label">信号日期：</span>
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 160px"
          />
        </div>
        <div class="filter-item">
          <span class="filter-label">策略类型：</span>
          <el-select v-model="selectedStrategyTypes" multiple placeholder="全部策略" style="width: 200px">
            <el-option label="突破策略" value="breakout" />
            <el-option label="动量策略" value="momentum" />
            <el-option label="多因子策略" value="multi_factor" />
            <el-option label="技术形态" value="technical" />
            <el-option label="反转策略" value="reversal" />
            <el-option label="均值回归" value="mean_reversion" />
          </el-select>
        </div>
      </div>
    </el-card>

    <!-- 信号列表 -->
    <div v-loading="loading" class="signals-container">
      <el-empty v-if="filteredSignals.length === 0" description="暂无买入信号" />
      
      <div v-if="filteredSignals.length > 0" class="signal-list">
        <div
          v-for="signal in filteredSignals"
          :key="signal.id"
          class="signal-card"
        >
          <!-- 左侧：信号信息 -->
          <div class="signal-info-section">
            <div class="signal-header">
              <div class="signal-title">
                <div class="stock-name">{{ signal.stock.name }}</div>
                <div class="stock-code">{{ signal.stock.tsCode }}</div>
                <div class="stock-tags">
                  <el-tag v-if="signal.stock.industry" size="small" type="info" class="industry-tag">
                    {{ signal.stock.industry }}
                  </el-tag>
                </div>
              </div>
              <div class="signal-badges">
                <div v-if="signal.stock.changePct !== undefined" class="change-badge" :class="getChangeClass(signal.stock.changePct)">
                  {{ (signal.stock.changePct > 0 ? '+' : '') + signal.stock.changePct.toFixed(2) }}%
                </div>
                <!-- <div class="strength-badge" :class="getStrengthClass(signal.strength)">
                  {{ signal.strength.toFixed(0) }}
                </div> -->
              </div>
            </div>

            <div class="signal-body">
              <!-- 价格信息 -->
              <div v-if="signal.priceRange" class="price-section">
                <div class="current-price">
                  <span class="label">当前价格</span>
                  <span class="value">¥{{ signal.priceRange.current.toFixed(2) }}</span>
                </div>
                <div v-if="signal.stopLoss" class="stop-loss">
                  <span class="label">止损价格</span>
                  <span class="value">¥{{ signal.stopLoss.toFixed(2) }}</span>
                </div>
              </div>

              <!-- 买入理由 -->
              <div class="reasons-section">
                <div class="reasons-list">
                  <div
                    v-for="reason in signal.reasons.slice(0, 3)"
                    :key="reason.title"
                    class="reason-item"
                    :class="{ satisfied: reason.satisfied }"
                  >
                    <el-icon v-if="reason.satisfied" class="check-icon"><CircleCheck /></el-icon>
                    <el-icon v-else class="info-icon"><InfoFilled /></el-icon>
                    <span class="reason-text">{{ reason.title }}</span>
                  </div>
                  <div v-if="signal.reasons.length > 3" class="more-reasons">
                    +{{ signal.reasons.length - 3 }} 个理由
                  </div>
                </div>
              </div>

            </div>

            <div class="signal-footer">
              <el-button size="small" @click="showDetail(signal)">
                详情
              </el-button>
            </div>
          </div>

          <!-- 右侧：K线图 -->
          <div class="signal-chart-section">
            <StockKlineChart
              :ref="(el) => { if (el) chartRefs.set(signal.stock.tsCode, el) }"
              :ts-code="signal.stock.tsCode"
              :kline-data="klineDataCache.get(signal.stock.tsCode) || []"
              min-height="260px"
            />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useBuyReferenceStore } from '@/stores/buyReference'
import { realtimeApi } from '@/api'
import StockKlineChart from '@/components/StockKlineChart.vue'
import { 
  Refresh, 
  CircleCheck, 
  InfoFilled
} from '@element-plus/icons-vue'
import type { BuySignal } from '@/types/buy-reference'

const store = useBuyReferenceStore()
const router = useRouter()

const { stats, filteredSignals, loading } = storeToRefs(store)

const selectedStrategyTypes = ref<string[]>([])
const selectedDate = ref<string>('')

// K线数据缓存
const klineDataCache = ref(new Map())
const chartRefs = ref(new Map())

// 获取K线数据
const fetchKlineData = async (tsCode: string) => {
  if (klineDataCache.value.has(tsCode)) return

  try {
    const response = await realtimeApi.getKline(tsCode, 'daily', 180)
    if (response.success && response.data && response.data.data) {
      klineDataCache.value.set(tsCode, response.data.data)
    }
  } catch (error) {
    console.error('Failed to load kline for', tsCode, error)
  }
}

// 批量获取所有信号的K线数据
const fetchAllKlineData = () => {
  nextTick(() => {
    filteredSignals.value.forEach(signal => {
      if (signal.stock.tsCode) {
        fetchKlineData(signal.stock.tsCode)
      }
    })
  })
}

onMounted(() => {
  const today = new Date().toISOString().split('T')[0]
  selectedDate.value = today
  store.selectedDate = today
  store.fetchSignals(today).then(() => {
    fetchAllKlineData()
  })
})

watch(selectedDate, (val) => {
  store.selectedDate = val
  store.fetchSignals(val || undefined).then(() => {
    fetchAllKlineData()
  })
})

watch(selectedStrategyTypes, (val) => {
  store.updateFilter({
    strategyTypes: val as any
  })
})

// 监听信号列表变化，获取新信号的K线数据
watch(filteredSignals, () => {
  fetchAllKlineData()
})

const getChangeClass = (changePct: number | undefined) => {
  if (changePct === undefined || changePct === null) return ''
  if (changePct > 0) return 'up'
  if (changePct < 0) return 'down'
  return ''
}

const getStrategyTypeTag = (type: string) => {
  const map: Record<string, string> = {
    'breakout': 'danger',
    'momentum': 'warning',
    'multi_factor': 'success',
    'technical': 'primary',
    'reversal': 'info',
    'mean_reversion': 'info'
  }
  return map[type] || 'info'
}

// 根据信号强度获取样式类
const getStrengthClass = (strength: number) => {
  if (strength >= 80) return 'high'
  if (strength >= 60) return 'medium'
  return 'low'
}

const formatDateTime = (date: Date) => {
  const d = new Date(date)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const showDetail = (signal: BuySignal) => {
  router.push(`/stock/${signal.stock.tsCode}`)
}

const refresh = () => {
  klineDataCache.value.clear()
  store.refresh().then(() => {
    fetchAllKlineData()
  })
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  chartRefs.value.forEach((chart: any) => {
    chart?.resize()
  })
}
window.addEventListener('resize', handleResize)

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.buy-reference-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-value.active {
  color: #67c23a;
}

.stat-value.watching {
  color: #e6a23c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 30px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.range-value {
  font-size: 14px;
  color: #909399;
  min-width: 60px;
}

.signals-container {
  min-height: 400px;
}

/* 信号列表 - 纵向排列 */
.signal-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 信号卡片 - 横向布局 */
.signal-card {
  display: flex;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 2px solid transparent;
  overflow: hidden;
  transition: all 0.3s ease;
}

.signal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

/* 左侧信息区域 */
.signal-info-section {
  flex: 0 0 320px;
  padding: 20px;
  background: #fafbfc;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.signal-title {
  flex: 1;
}

.stock-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stock-code {
  font-size: 13px;
  color: #909399;
}

.stock-tags {
  display: flex;
  gap: 6px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.industry-tag {
  font-size: 11px;
}

.strategy-tag {
  font-size: 11px;
}

.signal-badges {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.change-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  background-color: #f5f7fa;
  color: #606266;
}

.change-badge.up {
  background-color: #fef0f0;
  color: #f56c6c;
}

.change-badge.down {
  background-color: #f0f9eb;
  color: #67c23a;
}

.strength-badge {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.strength-badge.high {
  background: linear-gradient(135deg, #f56c6c 0%, #ff8c8c 100%);
}

.strength-badge.medium {
  background: linear-gradient(135deg, #e6a23c 0%, #f0c78a 100%);
}

.strength-badge.low {
  background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
}

.signal-body {
  flex: 1;
}

.price-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.price-section > div {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.price-section > div:last-child {
  margin-bottom: 0;
}

.price-section .label {
  font-size: 12px;
  color: #909399;
}

.price-section .value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.current-price .value {
  font-size: 20px;
  color: #409eff;
  font-weight: 700;
}

.stop-loss .value {
  color: #f56c6c;
  font-weight: 600;
}

.reasons-section {
  margin-bottom: 16px;
}

.reasons-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.reason-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #fff;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
}

.reason-item.satisfied {
  background-color: #f0f9eb;
  color: #67c23a;
}

.check-icon {
  color: #67c23a;
  font-size: 16px;
  flex-shrink: 0;
}

.info-icon {
  color: #909399;
  font-size: 16px;
  flex-shrink: 0;
}

.reason-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-reasons {
  font-size: 12px;
  color: #909399;
  text-align: center;
  padding: 4px;
}

.indicators-section {
  margin-bottom: 16px;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.indicator-item {
  background-color: #fff;
  border-radius: 6px;
  padding: 10px;
  text-align: center;
}

.indicator-name {
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.indicator-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.indicator-value.up {
  color: #67c23a;
}

.indicator-value.down {
  color: #f56c6c;
}

.time-section {
  font-size: 11px;
  color: #909399;
  text-align: center;
  margin-bottom: 12px;
}

.time-label {
  margin-right: 4px;
}

.signal-footer {
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: center;
}

/* 右侧图表区域 */
.signal-chart-section {
  flex: 1;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  min-height: 280px;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .signal-info-section {
    flex: 0 0 280px;
  }
}

@media (max-width: 992px) {
  .signal-card {
    flex-direction: column;
  }

  .signal-info-section {
    flex: none;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #ebeef5;
  }

  .signal-chart-section {
    min-height: 260px;
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .signal-info-section {
    padding: 16px;
  }

  .signal-chart-section {
    min-height: 220px;
    padding: 10px;
  }

  .current-price .value {
    font-size: 18px;
  }
}

@media (max-width: 480px) {
  .signal-header {
    flex-direction: column;
    gap: 10px;
  }

  .strength-badge {
    width: 40px;
    height: 40px;
    font-size: 14px;
  }

  .signal-chart-section {
    min-height: 200px;
  }
}

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
