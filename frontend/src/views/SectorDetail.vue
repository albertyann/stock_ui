<template>
  <div class="sector-detail-page">
    <!-- 返回按钮和标题 -->
    <div class="page-header">
      <el-button @click="goBack" link>
        <el-icon><ArrowLeft /></el-icon>返回板块列表
      </el-button>
    </div>

    <!-- 板块信息卡片 -->
    <el-card v-if="sectorInfo" class="sector-info-card">
      <div class="sector-header-info">
        <div class="sector-title">
          <span class="sector-name">{{ sectorInfo.name }}</span>
          <el-tag :type="sectorInfo.type === 'industry' ? 'success' : 'warning'" size="small">
            {{ sectorInfo.type === 'industry' ? '行业板块' : '概念板块' }}
          </el-tag>
        </div>
        <div class="sector-change" :class="getChangeClass(sectorInfo.change_pct)">
          {{ formatChange(sectorInfo.change_pct) }}
        </div>
      </div>
      <div class="sector-stats">
        <span>股票数: {{ sectorInfo.stock_count }}</span>
        <span>总成交量: {{ formatVolume(sectorInfo.total_volume) }}</span>
        <span>总成交额: {{ formatAmount(sectorInfo.total_amount) }}</span>
      </div>
    </el-card>

    <!-- 搜索和筛选区域 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="searchQuery"
          placeholder="搜索股票名称或代码，支持多支股票（逗号分隔）"
          clearable
          :prefix-icon="Search"
          @input="handleSearch"
          style="flex: 1; margin-right: 15px;"
        />
        <el-select
          v-model="sortOrder"
          placeholder="排序方式"
          style="width: 150px; margin-right: 10px;"
          @change="handleSortChange"
        >
          <el-option label="默认排序" value="default" />
          <el-option label="涨幅升序" value="asc" />
          <el-option label="涨幅降序" value="desc" />
          <el-option label="成交量升序" value="volume_asc" />
          <el-option label="成交量降序" value="volume_desc" />
        </el-select>
        <el-select
          v-model="trendFilter"
          placeholder="趋势筛选"
          style="width: 120px;"
          @change="handleTrendChange"
        >
          <el-option label="全部趋势" value="all" />
          <el-option label="上升趋势" value="up" />
          <el-option label="下降趋势" value="down" />
        </el-select>
      </div>
      <div v-if="searchQuery.trim() || trendFilter !== 'all'" class="search-info">
        <el-tag v-if="searchQuery.trim()" type="info">
          搜索: {{ stocks.length }} 条 / 共 {{ totalStocks }} 条
        </el-tag>
        <el-tag v-if="trendFilter !== 'all'" :type="trendFilter === 'up' ? 'danger' : 'success'" style="margin-left: 8px;">
          趋势: {{ trendFilter === 'up' ? '上升' : '下降' }}
        </el-tag>
      </div>
    </el-card>

    <!-- 股票列表 -->
    <div v-loading="loading" class="stocks-container">
      <el-empty v-if="!loading && stocks.length === 0 && hasSearched" description="暂无数据" />
      
      <template v-if="stocks.length > 0">
        <div class="pagination-row top">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="20"
            :total="totalStocks"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>

        <div class="stock-list">
          <div 
            v-for="(stock, index) in stocks" 
            :key="stock.ts_code"
            class="stock-card" 
            :class="[getChangeClass(stock.change_pct), { selected: index === selectedStockIndex }]"
            @click="selectedStockIndex = index"
          >
            <!-- 左侧：股票信息 -->
            <div class="stock-info-section">
              <div class="stock-header">
                <div class="stock-title">
                  <div class="stock-name">{{ stock.name }}</div>
                  <div class="stock-code">{{ stock.ts_code }}</div>
                  <el-tag v-if="stock.industry" size="small" type="info" class="industry-tag">
                    {{ stock.industry }}
                  </el-tag>
                </div>
                <div 
                  class="change-badge" 
                  :class="getChangeClass(stock.change_pct)"
                >
                  {{ formatChange(stock.change_pct) }}
                </div>
              </div>
              
              <div class="stock-body">
                <!-- 当前价格 -->
                <div class="price-section">
                  <div class="current-price" :class="getChangeClass(stock.change_pct)">
                    ¥{{ (stock.price ?? 0).toFixed(2) }}
                  </div>
                  <div class="change-info">
                    <span :class="getChangeClass(stock.change_pct)">
                      {{ (stock.change ?? 0) >= 0 ? '+' : '' }}{{ (stock.change ?? 0).toFixed(2) }}
                    </span>
                    <span :class="getChangeClass(stock.change_pct)">
                      ({{ (stock.change_pct ?? 0) >= 0 ? '+' : '' }}{{ (stock.change_pct ?? 0).toFixed(2) }}%)
                    </span>
                  </div>
                </div>
                
                <!-- 成交量信息 -->
                <div class="volume-section">
                  <div class="volume-row">
                    <span class="label">成交量</span>
                    <span class="value">{{ formatVolume(stock.volume) }}</span>
                  </div>
                  <div class="volume-row">
                    <span class="label">成交额</span>
                    <span class="value">{{ formatAmount(stock.amount) }}</span>
                  </div>
                </div>
                
                <!-- 盘口信息 -->
                <div class="bid-ask-section" v-if="stock.bid_price || stock.ask_price">
                  <div class="bid-ask-row">
                    <div class="bid">
                      <span class="label">买一</span>
                      <span class="value">{{ stock.bid_price ? '¥' + (stock.bid_price ?? 0).toFixed(2) : '-' }}</span>
                      <span class="volume">{{ stock.bid_volume || '' }}</span>
                    </div>
                    <div class="ask">
                      <span class="label">卖一</span>
                      <span class="value">{{ stock.ask_price ? '¥' + (stock.ask_price ?? 0).toFixed(2) : '-' }}</span>
                      <span class="volume">{{ stock.ask_volume || '' }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- 更新时间 -->
                <div class="time-section">
                  <span class="time-label">更新：</span>
                  <span class="time-value">{{ stock.update_time }}</span>
                  <span v-if="stock.trade_time" class="trade-time">
                    交易时间：{{ stock.trade_time }}
                  </span>
                </div>
              </div>
              
              <div class="stock-footer">
                
                <el-button
                  size="small"
                  type="warning"
                  @click="addToWatchlist(stock)"
                  :loading="stock.addingToWatchlist"
                  :disabled="stock.isWatched"
                >
                  {{ stock.isWatched ? '已关注' : '关注' }}
                </el-button>
                <el-button size="small" type="primary" link @click="viewDetail(stock)">
                  详情
                </el-button>
                <el-button size="small" type="primary" link @click="openXueqiu(stock)">
                  雪球
                </el-button>
              </div>
            </div>
            
            <!-- 右侧：K线图 -->
            <div class="stock-chart-section">
              <StockSimpleKlineChart
                :ref="(el) => { if (el) chartRefs.set(stock.ts_code, el) }"
                :ts-code="stock.ts_code"
                :kline-data="klineDataCache.get(stock.ts_code) || []"
                :show-volume="true"
                height="360px"
              />
            </div>
          </div>
        </div>

        <div class="pagination-row bottom">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="20"
            :total="totalStocks"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </template>
    </div>

    <!-- 关注股票弹窗 -->
    <FollowStockDialog
      v-model="followDialogVisible"
      :stock="currentFollowStock"
      @success="handleFollowSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onUnmounted, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Search } from '@element-plus/icons-vue'
import { realtimeApi, watchlistApi, sectorApi } from '@/api'
import { getChangeClass, formatChange, formatVolume, formatAmount, openXueqiu } from '@/utils/stock'
import { useStockKeyboardNav } from '@/composables/useStockKeyboardNav'
import StockSimpleKlineChart from '@/components/StockSimpleKlineChart.vue'
import FollowStockDialog from '@/components/FollowStockDialog.vue'

const router = useRouter()
const route = useRoute()

// 选中股票索引（用于键盘导航）
const selectedStockIndex = ref(0)

// 板块信息
const sectorInfo = ref(null)

// 搜索相关
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const stocks = ref([])
const loading = ref(false)
const hasSearched = ref(false)
const totalStocks = ref(0) // 后端分页总数
const sortOrder = ref('default') // 'default' | 'asc' | 'desc' | 'volume_asc' | 'volume_desc'
const trendFilter = ref('up') // 'all' | 'up' | 'down'

// 返回板块列表
const goBack = () => {
  router.push('/sectors')
}

// 分页处理
const handlePageChange = (page, skipScroll = false) => {
  currentPage.value = page
  selectedStockIndex.value = 0 // 重置选中索引到第一个
  fetchSectorStocks().then(() => {
    if (!skipScroll) {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })
}

// 排序变化处理
const handleSortChange = () => {
  selectedStockIndex.value = 0
  currentPage.value = 1
  fetchSectorStocks()
}

// 趋势筛选变化处理
const handleTrendChange = () => {
  selectedStockIndex.value = 0
  currentPage.value = 1
  fetchSectorStocks()
}

// 搜索处理
let searchTimeout = null
const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    fetchSectorStocks()
  }, 300)
}

// 数据缓存
const klineDataCache = ref(new Map())
const chartRefs = ref(new Map())

// 关注弹窗相关
const followDialogVisible = ref(false)
const currentFollowStock = ref(null)

// 打开关注弹窗
const openFollowDialog = (stock) => {
  currentFollowStock.value = stock
  followDialogVisible.value = true
}

const handleFollowSuccess = () => {
  followDialogVisible.value = false
  if (currentFollowStock.value) {
    currentFollowStock.value.isWatched = true
  }
}

// 获取板块股票列表
const fetchSectorStocks = async () => {
  const sectorCode = route.query.code
  const sectorType = route.query.sectorType || 'industry'

  if (!sectorCode) return

  loading.value = true
  hasSearched.value = true

  // 清理旧的数据缓存
  klineDataCache.value.clear()

  try {
    // 获取板块详情和股票列表（后端分页）
    const response = await sectorApi.getSectorStocks(
      sectorCode,
      sectorType,
      currentPage.value,
      20,
      searchQuery.value.trim() || null,
      sortOrder.value !== 'default' ? sortOrder.value : 'default',
      trendFilter.value !== 'all' ? trendFilter.value : null
    )

    if (response.success) {
      sectorInfo.value = response.data.sector
      stocks.value = response.data.stocks || []
      totalStocks.value = response.data.pagination?.total || 0

      if (stocks.value.length === 0) {
        ElMessage.info('该板块暂无股票数据')
      } else {
        ElMessage.success(`成功获取 ${stocks.value.length} 只股票数据（共 ${totalStocks.value} 条）`)
        // 检查关注状态
        checkWatchStatus(stocks.value)
        // 数据加载完成后获取K线数据
        nextTick(() => {
          stocks.value.forEach(stock => {
            fetchKlineData(stock.ts_code)
          })
        })
      }
    } else {
      ElMessage.error(response.error || '获取数据失败')
    }
  } catch (error) {
    console.error('Failed to fetch sector stocks:', error)
    ElMessage.error('获取板块股票失败：' + (error.response?.data?.detail || error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

// 批量获取K线数据
const fetchKlineData = async (tsCode) => {
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

// 检查股票是否已被关注
const checkWatchStatus = async (stockList) => {
  if (!stockList || stockList.length === 0) return

  const tsCodes = stockList.map(s => s.ts_code).filter(Boolean)
  if (tsCodes.length === 0) return

  try {
    const response = await watchlistApi.checkStocks(tsCodes)
    if (response.success && response.data && response.data.watched_codes) {
      const watchedSet = new Set(response.data.watched_codes)
      stockList.forEach(stock => {
        stock.isWatched = watchedSet.has(stock.ts_code)
      })
    }
  } catch (error) {
    console.error('Failed to check watch status:', error)
  }
}

// 监听路由参数变化
watch(() => route.query.code, (newCode) => {
  if (newCode) {
    fetchSectorStocks()
  } else {
    stocks.value = []
    sectorInfo.value = null
    searchQuery.value = ''
    currentPage.value = 1
    trendFilter.value = 'all'
  }
  selectedStockIndex.value = 0
}, { immediate: true })

// 页面加载时检查路由参数
onMounted(() => {
  if (route.query.code) {
    fetchSectorStocks()
  }
})

// 查看详情
const viewDetail = (stock) => {
  if (!stock.ts_code) return
  window.open(`/stock/${stock.ts_code}`, '_blank')
}

// 添加到关注列表
const addToWatchlist = (stock) => {
  openFollowDialog(stock)
}

// 注册股票列表键盘导航
useStockKeyboardNav({
  items: stocks,
  selectedIndex: selectedStockIndex,
  openXueqiu,
  addToWatchlist,
  pageTurn: {
    currentPage,
    pageSize,
    totalItems: totalStocks,
    onPageChange: handlePageChange
  }
})

// 窗口大小变化时重新调整图表
const handleResize = () => {
  chartRefs.value.forEach(chart => {
    chart.resize()
  })
}
window.addEventListener('resize', handleResize)

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.sector-detail-page {
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
  color: var(--text-primary);
  font-size: 24px;
}

/* 板块信息卡片 */
.sector-info-card {
  margin-bottom: 20px;
}

.sector-header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.sector-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sector-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.sector-change {
  font-size: 24px;
  font-weight: 700;
  padding: 8px 16px;
  border-radius: 8px;
}

.sector-change.up {
  color: var(--stock-up);
  background: rgba(239, 68, 68, 0.12);
}

.sector-change.down {
  color: var(--stock-down);
  background: rgba(34, 197, 94, 0.12);
}

.sector-change.flat {
  color: var(--stock-flat);
  background: rgba(100, 116, 139, 0.12);
}

.sector-stats {
  display: flex;
  gap: 30px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 筛选区域 */
.filter-card {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.search-info {
  margin-top: 10px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--accent);
  margin-bottom: 5px;
}

.stat-card.up .stat-value {
  color: var(--stock-up);
}

.stat-card.down .stat-value {
  color: var(--stock-down);
}

.stat-card.flat .stat-value {
  color: var(--stock-flat);
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

.stocks-container {
  min-height: 200px;
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
}

.pagination-row.top {
  margin-bottom: 16px;
}

.pagination-row.bottom {
  margin-top: 16px;
}

/* 股票列表 - 纵向排列 */
.stock-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 股票卡片 - 横向布局 */
.stock-card {
  display: flex;
  background: var(--bg-card-solid);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 2px solid transparent;
  overflow: hidden;
  transition: all 0.3s ease;
}

.stock-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stock-card.up {
  border-color: var(--stock-up);
}

.stock-card.down {
  border-color: var(--stock-down);
}

.stock-card.flat {
  border-color: var(--border-subtle);
}

.stock-card.selected {
  box-shadow: 0 8px 24px var(--accent-glow);
  border-color: var(--accent) !important;
  transform: translateY(-2px);
  position: relative;
}

.stock-card.selected::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--accent) 0%, var(--accent-cyan) 100%);
  border-radius: 12px 0 0 12px;
}

/* 左侧信息区域 */
.stock-info-section {
  flex: 0 0 320px;
  padding: 20px;
  background: var(--bg-input);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.stock-title {
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

.change-badge {
  width: 72px;
  height: 36px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.change-badge.up {
  background: linear-gradient(135deg, var(--stock-up) 0%, var(--stock-up) 100%);
  color: #fff !important;
}

.change-badge.down {
  background: linear-gradient(135deg, var(--stock-down) 0%, var(--stock-down) 100%);
  color: #fff !important;
}

.change-badge.flat {
  background: linear-gradient(135deg, var(--text-muted) 0%, var(--stock-flat) 100%);
  color: #fff !important;
}

.stock-body {
  flex: 1;
}

.price-section {
  text-align: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.current-price {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 6px;
}

.current-price.up {
  color: var(--stock-up);
}

.current-price.down {
  color: var(--stock-down);
}

.current-price.flat {
  color: var(--stock-flat);
}

.change-info {
  font-size: 13px;
}

.change-info .up {
  color: var(--stock-up);
}

.change-info .down {
  color: var(--stock-down);
}

.change-info .flat {
  color: var(--stock-flat);
}

.volume-section {
  margin-bottom: 12px;
}

.volume-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.volume-row:last-child {
  margin-bottom: 0;
}

.volume-row .label {
  font-size: 12px;
  color: var(--text-muted);
}

.volume-row .value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.bid-ask-section {
  background-color: var(--bg-card-solid);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 12px;
}

.bid-ask-row {
  display: flex;
  justify-content: space-between;
}

.bid, .ask {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.bid .label {
  color: var(--stock-down);
  font-size: 11px;
  font-weight: 600;
}

.ask .label {
  color: var(--stock-up);
  font-size: 11px;
  font-weight: 600;
}

.bid .value, .ask .value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.bid .volume, .ask .volume {
  font-size: 11px;
  color: var(--text-muted);
}

.time-section {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 12px;
}

.time-label {
  margin-right: 4px;
}

.trade-time {
  margin-left: 8px;
  color: var(--accent);
}

.stock-footer {
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}

/* 右侧图表区域 */
.stock-chart-section {
  flex: 1;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card-solid);
  min-height: 280px;
  overflow: hidden;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .stock-info-section {
    flex: 0 0 280px;
  }
}

@media (max-width: 992px) {
  .stock-card {
    flex-direction: column;
  }

  .stock-info-section {
    flex: none;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-subtle);
  }

  .stock-chart-section {
    min-height: 260px;
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .sector-detail-page {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .filter-row {
    flex-direction: column;
    gap: 10px;
  }

  .filter-row .el-input {
    margin-right: 0 !important;
    width: 100%;
  }

  .stock-info-section {
    padding: 16px;
  }

  .stock-chart-section {
    min-height: 220px;
    padding: 10px;
  }

  .current-price {
    font-size: 24px;
  }

  .bid-ask-section {
    padding: 8px;
  }

  .bid-ask-row {
    flex-direction: column;
    gap: 6px;
  }

  .bid, .ask {
    justify-content: space-between;
  }
}

@media (max-width: 480px) {
  .stock-header {
    flex-direction: column;
    gap: 10px;
  }

  .change-badge {
    width: 100%;
    height: 32px;
  }

  .stock-chart-section {
    min-height: 200px;
  }
}
</style>
