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
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.avgStrength.toFixed(1) }}</div>
          <div class="stat-label">平均强度</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 过滤器 -->
    <el-card class="filter-card">
      <div class="filter-row">
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
        <div class="filter-item">
          <span class="filter-label">信号强度：</span>
          <el-slider v-model="strengthRange" range :max="100" style="width: 200px" />
          <span class="range-value">{{ strengthRange[0] }} - {{ strengthRange[1] }}</span>
        </div>
      </div>
    </el-card>

    <!-- 信号卡片列表 -->
    <div v-loading="loading" class="signals-container">
      <el-empty v-if="filteredSignals.length === 0" description="暂无买入信号" />
      
      <el-row v-else :gutter="20">
        <el-col 
          v-for="signal in filteredSignals" 
          :key="signal.id"
          :xs="24" 
          :sm="12" 
          :md="8" 
          :lg="6"
          class="signal-col"
        >
          <el-card class="signal-card" :class="getStrengthClass(signal.strength)">
            <template #header>
              <div class="card-header">
                <div class="stock-info">
                  <div class="stock-name">{{ signal.stock.name }}</div>
                  <div class="stock-code">{{ signal.stock }}</div>
                </div>
                <div class="strength-badge" :class="getStrengthClass(signal.strength)">
                  {{ signal.strength }}
                </div>
              </div>
            </template>
            
            <div class="signal-content">
              <!-- 策略信息 -->
              <div class="strategy-section">
                <el-tag :type="getStrategyTypeTag(signal.strategy.type)" size="small" effect="dark">
                  {{ signal.strategy.name }}
                </el-tag>
              </div>
              
              <!-- 价格信息 -->
              <div v-if="signal.priceRange" class="price-section">
                <div class="current-price">
                  <span class="label">当前：</span>
                  <span class="value">¥{{ signal.priceRange.current.toFixed(2) }}</span>
                </div>
                <div class="target-price">
                  <span class="label">目标：</span>
                  <span class="value">¥{{ signal.priceRange.low.toFixed(2) }} - ¥{{ signal.priceRange.high.toFixed(2) }}</span>
                </div>
                <div v-if="signal.stopLoss" class="stop-loss">
                  <span class="label">止损：</span>
                  <span class="value">¥{{ signal.stopLoss.toFixed(2) }}</span>
                </div>
              </div>
              
              <!-- 买入理由 -->
              <div class="reasons-section">
                <div class="section-title">买入理由</div>
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
              
              <!-- 技术指标 -->
              <div v-if="signal.indicators" class="indicators-section">
                <div class="section-title">关键指标</div>
                <div class="indicators-grid">
                  <div v-if="signal.indicators.ma20" class="indicator-item">
                    <span class="indicator-name">MA20</span>
                    <span class="indicator-value">{{ signal.indicators.ma20.toFixed(2) }}</span>
                  </div>
                  <div v-if="signal.indicators.rsi" class="indicator-item">
                    <span class="indicator-name">RSI</span>
                    <span class="indicator-value">{{ signal.indicators.rsi.toFixed(1) }}</span>
                  </div>
                  <div v-if="signal.indicators.macd" class="indicator-item">
                    <span class="indicator-name">MACD</span>
                    <span class="indicator-value" :class="signal.indicators.macd > 0 ? 'up' : 'down'">
                      {{ signal.indicators.macd > 0 ? '+' : '' }}{{ signal.indicators.macd.toFixed(2) }}
                    </span>
                  </div>
                </div>
              </div>
              
              <!-- 生成时间 -->
              <div class="time-section">
                <span class="time-label">生成时间：</span>
                <span class="time-value">{{ formatDateTime(signal.createdAt) }}</span>
              </div>
            </div>
            
            <template #footer>
              <div class="card-footer">
                <el-button size="small" @click="showDetail(signal)">
                  <el-icon><View /></el-icon>详情
                </el-button>
                <el-button size="small" type="primary" @click="addToWatchlist(signal)">
                  <el-icon><Plus /></el-icon>观察池
                </el-button>
                <el-button size="small" type="danger" text @click="removeSignal(signal.id)">
                  <el-icon><Delete /></el-icon>移除
                </el-button>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="买入信号详情" width="700px" class="detail-dialog">
      <div v-if="selectedSignal" class="signal-detail">
        <div class="detail-header">
          <div class="stock-title">
            <div class="stock-name">{{ selectedSignal.stock.name }}</div>
            <div class="stock-code">{{ selectedSignal.stock.tsCode }}</div>
          </div>
          <div class="strength-large" :class="getStrengthClass(selectedSignal.strength)">
            {{ selectedSignal.strength }}
          </div>
        </div>
        
        <el-divider />
        
        <div class="detail-grid">
          <!-- 策略信息 -->
          <div class="detail-section">
            <h4><el-icon><Pointer /></el-icon>策略信息</h4>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="策略名称">{{ selectedSignal.strategy.name }}</el-descriptions-item>
              <el-descriptions-item label="策略类型">
                <el-tag :type="getStrategyTypeTag(selectedSignal.strategy.type)">{{ selectedSignal.strategy.type }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          
          <!-- 价格建议 -->
          <div v-if="selectedSignal.priceRange" class="detail-section">
            <h4><el-icon><PriceTag /></el-icon>价格建议</h4>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="当前价格">
                <span class="price-current">¥{{ selectedSignal.priceRange.current.toFixed(2) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="建议买入区间">
                <span class="price-target">¥{{ selectedSignal.priceRange.low.toFixed(2) }} - ¥{{ selectedSignal.priceRange.high.toFixed(2) }}</span>
              </el-descriptions-item>
              <el-descriptions-item v-if="selectedSignal.stopLoss" label="止损价格">
                <span class="price-stop">¥{{ selectedSignal.stopLoss.toFixed(2) }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        
        <!-- 买入理由详情 -->
        <div class="detail-section">
          <h4><el-icon><List /></el-icon>买入理由详情</h4>
          
          <div class="reasons-detail">
            <div 
              v-for="(reason, index) in selectedSignal.reasons" 
              :key="index"
              class="reason-detail-item"
              :class="{ satisfied: reason.satisfied }"
            >
              <div class="reason-header">
                <div class="reason-index">{{ index + 1 }}</div>
                <div class="reason-title-detail">{{ reason.title }}</div>
                <el-tag size="small" :type="reason.satisfied ? 'success' : 'info'">
                  {{ reason.satisfied ? '满足' : '参考' }}
                </el-tag>
              </div>
              
              <div class="reason-body">
                <p class="reason-description">{{ reason.description }}</p>
                
                <div v-if="reason.indicator" class="reason-metrics">
                  <div class="metric-item">
                    <span class="metric-label">指标：</span>
                    <span class="metric-value">{{ reason.indicator }}</span>
                  </div>
                  <div v-if="reason.value" class="metric-item">
                    <span class="metric-label">数值：</span>
                    <span class="metric-value highlight">{{ reason.value }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">权重：</span>
                    <span class="metric-value">{{ (reason.weight * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 技术指标 -->
        <div v-if="selectedSignal.indicators" class="detail-section">
          <h4><el-icon><TrendCharts /></el-icon>技术指标</h4>
          
          <div class="indicators-detail">
            <div 
              v-for="(value, key) in selectedSignal.indicators" 
              :key="key"
              class="indicator-card"
            >
              <div class="indicator-name-detail">{{ key.toUpperCase() }}</div>
              <div class="indicator-value-detail">
                {{ typeof value === 'number' ? value.toFixed(2) : value }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="addToWatchlist(selectedSignal); detailVisible = false">
          加入观察池
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useBuyReferenceStore } from '@/stores/buyReference'
import { useWatchlistStore } from '@/stores/watchlist'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, 
  Plus, 
  Delete, 
  View, 
  CircleCheck, 
  InfoFilled,
  Pointer,
  PriceTag,
  List,
  TrendCharts
} from '@element-plus/icons-vue'
import type { BuySignal } from '@/types/buy-reference'

const store = useBuyReferenceStore()
const watchlistStore = useWatchlistStore()

const { stats, filteredSignals, loading } = storeToRefs(store)

const detailVisible = ref(false)
const selectedSignal = ref<BuySignal | null>(null)
const selectedStrategyTypes = ref<string[]>([])
const strengthRange = ref([0, 100])

onMounted(() => {
  store.fetchSignals()
})

watch(selectedStrategyTypes, (val) => {
  store.updateFilter({
    strategyTypes: val as any
  })
})

watch(strengthRange, (val) => {
  store.updateFilter({
    minStrength: val[0],
    maxStrength: val[1]
  })
})

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

const getStrengthClass = (strength: number) => {
  if (strength >= 80) return 'strength-high'
  if (strength >= 60) return 'strength-medium'
  if (strength >= 40) return 'strength-low'
  return 'strength-weak'
}

const formatDateTime = (date: Date) => {
  const d = new Date(date)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const showDetail = (signal: BuySignal) => {
  selectedSignal.value = signal
  detailVisible.value = true
}

const refresh = () => {
  store.refresh()
}

const addToWatchlist = async (signal: BuySignal) => {
  try {
    const watchlistId = watchlistStore.watchlists.find(w => !w.is_default)?.id || watchlistStore.watchlists[0]?.id
    if (!watchlistId) {
      ElMessage.warning('请先创建一个观察池')
      return
    }
    
    await store.addToWatchlist(signal.id, watchlistId)
    ElMessage.success(`已将 ${signal.stock.name} 加入观察池`)
  } catch (error) {
    ElMessage.error('加入观察池失败')
  }
}

const removeSignal = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要移除这个买入信号吗？', '确认移除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await store.removeSignal(id)
    ElMessage.success('移除成功')
  } catch (error) {
    // 用户取消
  }
}
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

.signal-col {
  margin-bottom: 20px;
}

.signal-card {
  height: 100%;
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.signal-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.signal-card.strength-high {
  border-color: #67c23a;
}

.signal-card.strength-medium {
  border-color: #e6a23c;
}

.signal-card.strength-low {
  border-color: #409eff;
}

.signal-card.strength-weak {
  border-color: #dcdfe6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.stock-info {
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

.strength-badge {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: white;
}

.strength-badge.strength-high {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.strength-badge.strength-medium {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
}

.strength-badge.strength-low {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.strength-badge.strength-weak {
  background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
}

.signal-content {
  padding: 16px 0;
}

.strategy-section {
  margin-bottom: 16px;
}

.price-section {
  background-color: #f5f7fa;
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
  font-size: 13px;
  color: #909399;
}

.price-section .value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.current-price .value {
  font-size: 18px;
  color: #409eff;
  font-weight: 600;
}

.stop-loss .value {
  color: #f56c6c;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.reasons-section {
  margin-bottom: 16px;
}

.reasons-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reason-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
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
}

.info-icon {
  color: #909399;
  font-size: 16px;
}

.reason-text {
  flex: 1;
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
  gap: 10px;
}

.indicator-item {
  background-color: #f5f7fa;
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
  font-size: 12px;
  color: #909399;
  text-align: right;
}

.time-label {
  margin-right: 4px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-footer .el-button {
  flex: 1;
  margin: 0 4px;
}

/* 详情对话框样式 */
.detail-dialog :deep(.el-dialog__body) {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

.signal-detail {
  padding: 0 10px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stock-title {
  flex: 1;
}

.stock-title .stock-name {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.stock-title .stock-code {
  font-size: 14px;
  color: #909399;
}

.strength-large {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: bold;
  color: white;
}

.strength-large.strength-high {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.strength-large.strength-medium {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
}

.strength-large.strength-low {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.strength-large.strength-weak {
  background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.detail-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.detail-section h4 .el-icon {
  font-size: 18px;
  color: #409eff;
}

.price-current {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.price-target {
  font-size: 14px;
  font-weight: 500;
  color: #67c23a;
}

.price-stop {
  font-size: 14px;
  font-weight: 500;
  color: #f56c6c;
}

.reasons-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reason-detail-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.reason-detail-item.satisfied {
  border-color: #67c23a;
  background-color: #f0f9eb;
}

.reason-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.reason-detail-item.satisfied .reason-header {
  background-color: #e1f3d8;
  border-color: #67c23a;
}

.reason-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: #909399;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.reason-detail-item.satisfied .reason-index {
  background-color: #67c23a;
}

.reason-title-detail {
  flex: 1;
  font-weight: 600;
  color: #303133;
}

.reason-body {
  padding: 16px;
}

.reason-description {
  margin: 0 0 12px 0;
  color: #606266;
  line-height: 1.6;
}

.reason-metrics {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.metric-item {
  font-size: 13px;
}

.metric-label {
  color: #909399;
}

.metric-value {
  color: #606266;
  font-weight: 500;
}

.metric-value.highlight {
  color: #409eff;
  font-weight: 600;
}

.indicators-detail {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.indicator-card {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.indicator-name-detail {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.indicator-value-detail {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

@media (max-width: 768px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .indicators-detail {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
