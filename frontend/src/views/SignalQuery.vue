<template>
  <div class="page-container">

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="信号类型">
          <el-select
            v-model="filter.strategy_name"
            placeholder="全部策略"
            clearable
            style="width: 220px"
            @change="handleFilterChange"
          >
            <el-option
              v-for="s in meta.strategies"
              :key="s"
              :label="s"
              :value="s"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="信号日期">
          <el-date-picker
            v-model="filter.signal_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            clearable
            @change="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="市场">
          <el-radio-group v-model="filter.market_type" @change="handleFilterChange">
            <el-radio-button label="主板" value="main" />
            <el-radio-button label="创业" value="chye" />
            <el-radio-button label="科创" value="kcb" />
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-empty
        v-if="!loading && signals.length === 0"
        description="暂无信号数据"
      />

      <div v-if="signals.length > 0" class="signal-list">
        <div
          v-for="signal in signals"
          :key="signal.id"
          class="signal-card"
          :class="getSignalCardClass(signal)"
        >
          <!-- 左侧：信号信息 -->
          <div class="signal-info-section">
            <div class="signal-header">
              <div class="signal-title">
                <div class="stock-name">{{ signal.name || '-' }}</div>
                <div class="stock-code">{{ signal.ts_code }}</div>
                <el-tag v-if="signal.industry" size="small" type="info" class="industry-tag">
                  {{ signal.industry }}
                </el-tag>
                <el-tag
                  v-if="getMarketType(signal.ts_code)"
                  size="small"
                  :type="getMarketTypeTag(getMarketType(signal.ts_code))"
                  class="market-tag"
                >
                  {{ getMarketType(signal.ts_code) }}
                </el-tag>
              </div>
              <el-tag type="primary" size="large" class="strategy-tag">
                {{ signal.strategy_name || '-' }}
              </el-tag>
            </div>

            <div class="signal-body">
              <div class="signal-meta">
                <div class="meta-row">
                  <span class="label">信号日期</span>
                  <span class="value">{{ signal.signal_date || '-' }}</span>
                </div>
                <div class="meta-row">
                  <span class="label">评分</span>
                  <span class="value">{{ formatScore(signal.score) }}</span>
                </div>
                <div class="meta-row" v-if="signal['close_T+0'] != null">
                  <span class="label">T日收盘</span>
                  <span class="value">{{ formatPrice(signal['close_T+0']) }}</span>
                </div>
                <div class="meta-row" v-if="signal['change_T+0'] != null">
                  <span class="label">T日涨跌</span>
                  <span class="value" :class="getChangeClass(signal['change_T+0'])">
                    {{ formatChange(signal['change_T+0']) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="signal-footer">
              <el-button type="primary" size="small" link @click="viewDetail(signal)">
                详情
              </el-button>
              <el-button type="primary" size="small" link @click="openXueqiu(signal)">
                雪球
              </el-button>
            </div>
          </div>

          <!-- 右侧：K线图 -->
          <div class="signal-chart-section">
            <StockSimpleKlineChart
              :ref="(el) => { if (el) chartRefs.set(signal.id, el) }"
              :ts-code="signal.ts_code"
              :kline-data="klineDataCache.get(signal.id) || []"
              :show-volume="true"
              height="360px"
            />
          </div>
        </div>
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 30, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { trendApi, screeningApi, realtimeApi } from '@/api'
import { getMarketType, getMarketTypeTag, getChangeClass, formatChange, openXueqiu } from '@/utils/stock'
import { forwardAdjustKlineData } from '@/utils/kline'
import StockSimpleKlineChart from '@/components/StockSimpleKlineChart.vue'

const loading = ref(false)
const signals = ref([])

const filter = reactive({
  strategy_name: null,
  signal_date: null,
  market_type: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

const meta = reactive({
  strategies: []
})

// K线数据缓存: signal.id -> kline bars
const klineDataCache = ref(new Map())
const chartRefs = ref(new Map())

const fetchMeta = async () => {
  try {
    const res = await screeningApi.getResultsMeta()
    if (res.data) {
      meta.strategies = res.data.strategies || []
    }
  } catch (err) {
    console.error('Failed to fetch meta:', err)
  }
}

const fetchData = async () => {
  loading.value = true
  klineDataCache.value.clear()
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      strategy_name: filter.strategy_name || null,
      date_start: filter.signal_date || null,
      date_end: filter.signal_date || null,
      market_type: filter.market_type || null
    }
    const res = await trendApi.getTrends(params)
    if (res.success) {
      signals.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total
        pagination.total_pages = res.pagination.total_pages
      }
      if (signals.value.length > 0) {
        nextTick(() => {
          signals.value.forEach(signal => {
            fetchKlineData(signal)
          })
        })
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
    }
  } catch (err) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const fetchKlineData = async (signal) => {
  if (klineDataCache.value.has(signal.id)) return
  try {
    const response = await realtimeApi.getKline(signal.ts_code, 'daily', 120)
    if (response.success && response.data && response.data.data) {
      const adjustedData = forwardAdjustKlineData(response.data.data)
      klineDataCache.value.set(signal.id, adjustedData)
    }
  } catch (error) {
    console.error('Failed to load kline for', signal.ts_code, error)
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

const resetFilter = () => {
  filter.strategy_name = null
  filter.signal_date = null
  filter.market_type = null
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

const viewDetail = (signal) => {
  if (!signal.ts_code) return
  window.open(`/stock/${signal.ts_code}`, '_blank')
}

const formatPrice = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(2)
}

const formatScore = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(2)
}

const getSignalCardClass = (signal) => {
  if (signal['change_T+0'] == null) return ''
  if (signal['change_T+0'] > 0) return 'up'
  if (signal['change_T+0'] < 0) return 'down'
  return 'flat'
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  chartRefs.value.forEach(chart => {
    chart.resize()
  })
}

onMounted(() => {
  fetchMeta()
  fetchData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.filter-card {
  margin-bottom: 20px;
}

.signal-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 信号卡片 - 横向布局（参考 RealtimePrice.vue 股票卡片） */
.signal-card {
  display: flex;
  background: var(--bg-card-solid);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow-card);
  border: 2px solid transparent;
  overflow: hidden;
  transition: all 0.3s ease;
}

.signal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px var(--shadow-hover);
}

.signal-card.up {
  border-color: var(--stock-up);
}

.signal-card.down {
  border-color: var(--stock-down);
}

.signal-card.flat {
  border-color: var(--border-subtle);
}

/* 左侧信息区域 */
.signal-info-section {
  flex: 0 0 320px;
  padding: 20px;
  background: var(--bg-input);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 8px;
}

.signal-title {
  flex: 1;
}

.stock-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stock-code {
  font-size: 13px;
  color: var(--text-muted);
}

.industry-tag {
  margin-top: 6px;
  font-size: 11px;
}

.market-tag {
  margin-top: 6px;
  margin-left: 4px;
  font-size: 11px;
}

.strategy-tag {
  flex-shrink: 0;
  max-width: 110px;
}

.signal-body {
  flex: 1;
}

.signal-meta {
  margin-bottom: 12px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.meta-row:last-child {
  margin-bottom: 0;
}

.meta-row .label {
  font-size: 12px;
  color: var(--text-muted);
}

.meta-row .value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.meta-row .value.up {
  color: var(--stock-up);
}

.meta-row .value.down {
  color: var(--stock-down);
}

.signal-footer {
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}

/* 右侧图表区域 */
.signal-chart-section {
  flex: 1;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card-solid);
  min-height: 280px;
  overflow: hidden;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式布局 */
@media (max-width: 992px) {
  .signal-card {
    flex-direction: column;
  }

  .signal-info-section {
    flex: none;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-subtle);
  }

  .signal-chart-section {
    min-height: 260px;
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .page-container {
    padding: 12px;
  }

  .signal-info-section {
    padding: 16px;
  }

  .signal-chart-section {
    min-height: 220px;
    padding: 10px;
  }
}
</style>
