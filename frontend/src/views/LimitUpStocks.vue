<template>
  <div class="limit-up-page">
    <div class="page-header">
      <h2>涨停股票</h2>
      <div class="header-actions">
        <el-tag type="info" size="large" v-if="tradeDate">
          当前日期: {{ tradeDate }}
        </el-tag>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <div class="filter-item">
          <span class="filter-label">日期:</span>
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="true"
            @change="handleDateChange"
            style="width: 150px"
          />
        </div>
        <div class="filter-item">
          <span class="filter-label">板块:</span>
          <el-select
            v-model="selectedIndustry"
            placeholder="全部板块"
            :clearable="true"
            filterable
            @change="handleIndustryChange"
            style="width: 160px"
          >
            <el-option
              v-for="item in industryOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">搜索:</span>
          <el-input
            v-model="searchQuery"
            placeholder="输入股票代码或名称"
            clearable
            style="width: 200px"
            :prefix-icon="Search"
          />
        </div>
        <el-button type="primary" @click="fetchLimitUpStocks" :loading="loading">
          <el-icon><Refresh /></el-icon>查询
        </el-button>
        <el-button @click="resetFilters">
          重置
        </el-button>
      </div>
    </el-card>

    <!-- 统计信息和分页 -->
    <el-row :gutter="20" class="stats-row" v-if="filteredStocks.length > 0">
      <el-col :xs="24" :sm="8" :md="8" :lg="8">
        <el-card class="stat-card">
          <div class="stat-value">{{ filteredStocks.length }}</div>
          <div class="stat-label">涨停股票</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8" :md="8" :lg="8">
        <el-card class="stat-card up">
          <div class="stat-value">{{ maxChangePct }}%</div>
          <div class="stat-label">最高涨幅</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8" :md="8" :lg="8">
        <el-card class="stat-card">
          <div class="stat-value">{{ avgChangePct }}%</div>
          <div class="stat-label">平均涨幅</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页组件 -->
    <div class="pagination-wrapper" v-if="filteredStocks.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="filteredStocks.length"
        layout="total, sizes, prev, pager, next"
        :page-sizes="[50, 100, 200]"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 股票列表 -->
    <div v-loading="loading" class="stocks-container">
      <el-empty v-if="!loading && stocks.length === 0 && hasLoaded" description="今日无涨停股票" />
      
      <div v-if="paginatedStocks.length > 0" class="stock-list">
        <div 
          v-for="(stock, index) in paginatedStocks" 
          :key="stock.ts_code"
          class="stock-card" 
          :class="[getChangeClass(stock.change_pct), { selected: index === selectedStockIndex }]"
          @click="selectedStockIndex = index"
        >
          <!-- 左侧：股票信息 -->
          <div class="stock-info-section">
            <div class="stock-header">
              <div class="stock-title">
                <div class="stock-name">
                  {{ stock.name }}
                </div>
                <div class="stock-code">
                  {{ stock.ts_code }}
                </div>
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
                  {{ stock.price.toFixed(2) }}
                </div>
                <div class="change-info">
                  <span :class="getChangeClass(stock.change_pct)">
                    {{ stock.change >= 0 ? '+' : '' }}{{ stock.change.toFixed(2) }}
                  </span>
                  <span :class="getChangeClass(stock.change_pct)">
                    ({{ stock.change_pct >= 0 ? '+' : '' }}{{ stock.change_pct.toFixed(2) }}%)
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
              
              <!-- 更新时间 -->
              <div class="time-section">
                <span class="time-label">更新：</span>
                <span class="time-value">{{ stock.updated_at }}</span>
                <span class="trade-date">
                  交易日：{{ stock.trade_date }}
                </span>
              </div>
            </div>
            
            <div class="stock-footer">
              <el-button size="small" type="warning" @click="addToWatchlist(stock)" :loading="stock.addingToWatchlist" :disabled="stock.isWatched">
                {{ stock.isWatched ? '已关注' : '关注' }}
              </el-button>
              <el-button size="small" type="primary" link  @click="viewDetail(stock)">
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
    </div>

    <!-- 底部分页组件 -->
    <div class="pagination-wrapper" v-if="filteredStocks.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="filteredStocks.length"
        layout="total, sizes, prev, pager, next"
        :page-sizes="[50, 100, 200]"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
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
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { realtimeApi, sectorApi, watchlistApi } from '@/api'
import StockSimpleKlineChart from '@/components/StockSimpleKlineChart.vue'
import FollowStockDialog from '@/components/FollowStockDialog.vue'
import { forwardAdjustKlineData } from '@/utils/kline'
import { getChangeClass, formatChange, formatVolume, formatAmount, openXueqiu } from '@/utils/stock'
import { useStockKeyboardNav } from '@/composables/useStockKeyboardNav'

const router = useRouter()

const stocks = ref([])
const loading = ref(false)
const hasLoaded = ref(false)
const tradeDate = ref('')

// 分页相关
const currentPage = ref(1)
const pageSize = ref(50)

// 选中股票索引（用于键盘导航）
const selectedStockIndex = ref(0)

// 筛选相关
const selectedDate = ref('')
const selectedIndustry = ref('')
const industryOptions = ref([])
const searchQuery = ref('')

// 根据搜索关键词过滤股票列表
const filteredStocks = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return stocks.value
  return stocks.value.filter(stock => {
    const tsCode = stock.ts_code?.toLowerCase() || ''
    const name = stock.name?.toLowerCase() || ''
    return tsCode.includes(query) || name.includes(query)
  })
})

// 计算统计数据
const maxChangePct = computed(() => {
  if (filteredStocks.value.length === 0) return '0.00'
  const max = Math.max(...filteredStocks.value.map(s => s.change_pct))
  return max.toFixed(2)
})

const avgChangePct = computed(() => {
  if (filteredStocks.value.length === 0) return '0.00'
  const avg = filteredStocks.value.reduce((sum, s) => sum + s.change_pct, 0) / filteredStocks.value.length
  return avg.toFixed(2)
})

// 分页后的股票列表
const paginatedStocks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredStocks.value.slice(start, end)
})

// 分页处理
const handlePageChange = (page) => {
  currentPage.value = page
  selectedStockIndex.value = 0 // 重置选中索引到第一个
  // 滚动到列表顶部
  const stockListEl = document.querySelector('.stock-list')
  if (stockListEl) {
    stockListEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

// 获取涨停股票数据
const fetchLimitUpStocks = async () => {
  loading.value = true
  hasLoaded.value = true
  currentPage.value = 1 // 重置到第一页
  selectedStockIndex.value = 0 // 重置选中索引到第一个

  // 清理旧的数据缓存
  klineDataCache.value.clear()

  try {
    const params = {
      minChangePct: 9.9,
      limit: 200,
      tradeDate: selectedDate.value || null,
      industry: selectedIndustry.value || null
    }
    const response = await realtimeApi.getLimitUpStocks(params)
    if (response.success) {
      stocks.value = response.data || []
      tradeDate.value = response.trade_date || ''

      // 提取板块列表（用于筛选下拉框）
      updateIndustryOptions(stocks.value)

      if (stocks.value.length === 0) {
        ElMessage.info(selectedDate.value ? '该日期无涨停股票' : '今日无涨停股票')
      } else {
        const dateLabel = selectedDate.value || tradeDate.value
        ElMessage.success(`${dateLabel} 共 ${stocks.value.length} 只涨停股票`)
        // 检查关注状态
        checkWatchStatus(stocks.value)
        // 数据加载完成后获取K线数据
        nextTick(() => {
          paginatedStocks.value.forEach(stock => {
            fetchKlineData(stock.ts_code)
          })
        })
      }
    } else {
      ElMessage.error(response.error || '获取数据失败')
    }
  } catch (error) {
    console.error('Failed to fetch limit up stocks:', error)
    ElMessage.error('获取涨停股票失败：' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

// 获取K线数据
const fetchKlineData = async (tsCode) => {
  if (klineDataCache.value.has(tsCode)) return
  
  try {
    // 获取180天K线数据
    const response = await realtimeApi.getKline(tsCode, 'daily', 180)
    if (response.success && response.data && response.data.data) {
      // 使用前复权处理K线价格，消除送股、配股、分红等事件的影响
      const adjustedData = forwardAdjustKlineData(response.data.data)
      klineDataCache.value.set(tsCode, adjustedData)
    }
    
  } catch (error) {
    console.error('Failed to load kline for', tsCode, error)
  }
}

// 更新板块选项列表
const updateIndustryOptions = (stockList) => {
  const industries = new Set()
  stockList.forEach(stock => {
    if (stock.industry) {
      industries.add(stock.industry)
    }
  })
  industryOptions.value = Array.from(industries).sort()
}

// 从API获取所有板块列表
const fetchIndustryOptions = async () => {
  try {
    const response = await sectorApi.getAllSectors()
    if (response.success && response.data) {
      // 从板块数据中提取行业名称
      const industries = response.data.map(sector => sector.name).filter(name => name)
      industryOptions.value = industries.sort()
    }
  } catch (error) {
    console.error('Failed to fetch industry options:', error)
    // 如果API调用失败，保持使用从股票数据中提取的方式
  }
}

// 日期变更处理
const handleDateChange = () => {
  fetchLimitUpStocks()
}

// 板块变更处理
const handleIndustryChange = () => {
  // 前端筛选（如果后端返回所有数据）
  // 或者调用后端筛选（当前实现）
  fetchLimitUpStocks()
}

// 重置筛选
const resetFilters = () => {
  selectedDate.value = ''
  selectedIndustry.value = ''
  searchQuery.value = ''
  fetchLimitUpStocks()
}

// 搜索时重置到第一页
watch(searchQuery, () => {
  currentPage.value = 1
})

// 当分页股票变化时，获取新股票的K线数据
watch(paginatedStocks, (newStocks) => {
  nextTick(() => {
    newStocks.forEach(stock => {
      if (!klineDataCache.value.has(stock.ts_code)) {
        fetchKlineData(stock.ts_code)
      }
    })
  })
}, { immediate: true })

// 查看详情
const viewDetail = (stock) => {
  const resolved = router.resolve(`/stock/${stock.ts_code}`)
  window.open(resolved.href, '_blank')
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

// 添加到关注列表
const addToWatchlist = async (stock) => {
  stock.addingToWatchlist = true
  await openFollowDialog(stock)
  stock.addingToWatchlist = false
}

// 注册股票列表键盘导航
useStockKeyboardNav({
  items: paginatedStocks,
  selectedIndex: selectedStockIndex,
  openXueqiu,
  addToWatchlist
})

// 数据缓存
const klineDataCache = ref(new Map())
const chartRefs = ref(new Map())

// 窗口大小变化时重新调整图表
const handleResize = () => {
  chartRefs.value.forEach(chart => {
    chart.resize()
  })
}
// 组件挂载时加载数据和注册全局监听
onMounted(() => {
  fetchLimitUpStocks()
  fetchIndustryOptions()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.limit-up-page {
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 筛选栏样式 */
.filter-card {
  margin-bottom: 20px;
  background-color: var(--bg-input);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.stats-row {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  padding: 10px 0;
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
  color: var(--text-muted);
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

.stocks-container {
  min-height: 200px;
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
  box-shadow: 0 2px 12px var(--shadow-card);
  border: 2px solid transparent;
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
}

.stock-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px var(--shadow-hover);
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
}

.change-badge.down {
  background: linear-gradient(135deg, var(--stock-down) 0%, var(--stock-down) 100%);
}

.change-badge.flat {
  background: linear-gradient(135deg, var(--text-muted) 0%, var(--stock-flat) 100%);
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
  color: var(--text-muted);
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
  color: var(--text-muted);
}

.price-details {
  background-color: var(--bg-card-solid);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-row .label {
  font-size: 12px;
  color: var(--text-muted);
}

.detail-row .value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.detail-row .value.up {
  color: var(--stock-up);
}

.detail-row .value.down {
  color: var(--stock-down);
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

.time-section {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 12px;
}

.time-label {
  margin-right: 4px;
}

.trade-date {
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
    min-height: 360px;
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .limit-up-page {
    padding: 12px;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .filter-item {
    width: 100%;
  }

  .filter-item .el-date-picker,
  .filter-item .el-select {
    width: 100% !important;
  }

  .stock-info-section {
    padding: 16px;
  }

  .stock-chart-section {
    min-height: 300px;
    padding: 10px;
  }

  .current-price {
    font-size: 24px;
  }

  .price-details {
    padding: 8px;
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
    min-height: 240px;
  }
}
</style>
