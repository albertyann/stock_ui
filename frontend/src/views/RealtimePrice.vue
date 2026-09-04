<template>
  <div class="realtime-price-page">

    <!-- 板块信息卡片 -->
    <el-card v-if="isSectorMode && sectorInfo" class="sector-info-card">
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
    <el-card class="filter-card" v-if="isSectorMode">
      <!-- 周期选择：默认日线，可切换到周线 -->
      <div class="chart-options-bar">
        <div class="chart-options">
          <span class="options-label">K线周期</span>
          <el-radio-group v-model="klinePeriod" size="small" @change="handleKlinePeriodChange">
            <el-radio-button label="daily">日线</el-radio-button>
            <el-radio-button label="weekly">周线</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div class="filter-row">
        <el-input
          v-model="searchQuery"
          placeholder="搜索股票名称或代码，支持多支股票（逗号分隔）"
          clearable
          :prefix-icon="Search"
          @input="handleSearch"
          style="flex: 1; margin-right: 15px;"
        />
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="20"
          :total="totalStocks"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
      <div v-if="searchQuery.trim()" class="search-info">
        <el-tag type="info">
          搜索结果: {{ stocks.length }} 条 / 共 {{ totalStocks }} 条
        </el-tag>
      </div>
    </el-card>

    <!-- 普通模式：输入区域 -->
    <el-card v-if="!isSectorMode" class="input-card">
      <template #header>
        <div class="input-header">
          <div class="input-header-left">
            <span>股票输入</span>
            <el-tag type="info" size="small">支持股票代码或名称，一行一个</el-tag>
          </div>
          <!-- 周期选择：默认日线，可切换到周线 -->
          <div class="chart-options">
            <span class="options-label">K线周期</span>
            <el-radio-group v-model="klinePeriod" size="small" @change="handleKlinePeriodChange">
              <el-radio-button label="daily">日线</el-radio-button>
              <el-radio-button label="weekly">周线</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <!-- 最近查询历史（最多 5 条，点击回填输入框） -->
      <div v-if="queryHistory.length > 0" class="history-row">
        <span class="history-label">最近查询：</span>
        <el-tag
          v-for="item in queryHistory"
          :key="item.timestamp + '-' + item.text"
          class="history-tag"
          size="small"
          :title="item.text"
          closable
          @close="removeHistoryQuery(item)"
          @click="applyHistoryQuery(item)"
        >
          {{ shortQueryText(item.text) }}
        </el-tag>
        <el-button link type="primary" size="small" class="history-clear" @click="clearQueryHistory">
          清空
        </el-button>
      </div>

      <el-input
        v-model="stockInput"
        type="textarea"
        :rows="4"
        placeholder="请输入股票代码或名称，如：&#10;600000.SH&#10;000001.SZ&#10;或&#10;平安银行&#10;贵州茅台"
        :disabled="loading"
      />

      <div class="input-actions">
        <el-button
          type="primary"
          @click="fetchPrices"
          :loading="loading"
          :disabled="!stockInput.trim()"
        >
          查询实时价格
        </el-button>
        <div class="parsed-info" v-if="parsedCodes.length > 0">
          <el-tag type="success">已解析 {{ parsedCodes.length }} 个</el-tag>
        </div>
      </div>
    </el-card>

    <!-- 统计信息 -->
    <el-row :gutter="20" class="stats-row" v-if="stocks.length > 0">
      <el-col :xs="12" :sm="6" :md="6" :lg="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stocks.length }}</div>
          <div class="stat-label">关注股票</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6">
        <el-card class="stat-card up">
          <div class="stat-value">{{ upCount }}</div>
          <div class="stat-label">上涨</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6">
        <el-card class="stat-card down">
          <div class="stat-value">{{ downCount }}</div>
          <div class="stat-label">下跌</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6">
        <el-card class="stat-card flat">
          <div class="stat-value">{{ flatCount }}</div>
          <div class="stat-label">平盘</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 行业分布统计（当前查询股票中出现最多的前 3 个行业） -->
    <el-card v-if="stocks.length > 0 && topIndustries.length > 0" class="industry-stats-card">
      <div class="industry-stats-header">
        <span class="industry-stats-title">热门行业</span>
        <span class="industry-stats-subtitle">当前查询股票的行业分布 TOP{{ topIndustries.length }}</span>
      </div>
      <div class="industry-stats-list">
        <div v-for="item in topIndustries" :key="item.name" class="industry-stats-item">
          <span class="industry-stats-name">{{ item.name }}</span>
          <div class="industry-stats-bar-track">
            <div
              class="industry-stats-bar"
              :style="{ width: (item.count / topIndustries[0].count * 100) + '%' }"
            ></div>
          </div>
          <el-tag size="small" type="info" class="industry-stats-count">{{ item.count }} 只</el-tag>
        </div>
      </div>
    </el-card>

    <!-- 股票列表 -->
    <div v-loading="loading" class="stocks-container">
      <el-empty v-if="!loading && stocks.length === 0 && hasSearched" description="暂无数据" />
      
      <div v-if="stocks.length > 0" class="stock-list">
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
                <el-tag v-if="getMarketType(stock.ts_code)" size="small" :type="getMarketTypeTag(getMarketType(stock.ts_code))" class="market-tag">
                  {{ getMarketType(stock.ts_code) }}
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
              :kline-data="getKlineData(stock.ts_code)"
              :show-volume="true"
              height="360px"
            />
          </div>
        </div>
      </div>
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
import { Search } from '@element-plus/icons-vue'
import { realtimeApi, watchlistApi, sectorApi } from '@/api'
import { getMarketType, getMarketTypeTag, getChangeClass, formatChange, formatVolume, formatAmount, openXueqiu } from '@/utils/stock'
import { forwardAdjustKlineData } from '@/utils/kline'
import { useStockKeyboardNav } from '@/composables/useStockKeyboardNav'
import StockSimpleKlineChart from '@/components/StockSimpleKlineChart.vue'
import FollowStockDialog from '@/components/FollowStockDialog.vue'

const router = useRouter()
const route = useRoute()

// 选中股票索引（用于键盘导航）
const selectedStockIndex = ref(0)

// 判断是否为板块模式
const isSectorMode = computed(() => !!route.query.sector)

// 板块信息
const sectorInfo = ref(null)

// 搜索相关
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const stockInput = ref('')
const stocks = ref([])
const loading = ref(false)
const hasSearched = ref(false)
const totalStocks = ref(0) // 后端分页总数

// 查询历史缓存（localStorage）：每次查询后记录，页面刷新时恢复“当天最后一次查询”，最多记住 5 条
const QUERY_HISTORY_KEY = 'realtime_price_query_history'
const MAX_QUERY_HISTORY = 5

const queryHistory = ref([])

// 获取本地日期 YYYY-MM-DD（避免 toISOString 的 UTC 时区偏移导致“当天”错位）
const getTodayKey = () => {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const loadQueryHistory = () => {
  try {
    const stored = localStorage.getItem(QUERY_HISTORY_KEY)
    queryHistory.value = stored ? JSON.parse(stored) : []
  } catch (e) {
    console.warn('Failed to load query history:', e)
    queryHistory.value = []
  }
}

const saveQueryHistory = () => {
  try {
    localStorage.setItem(QUERY_HISTORY_KEY, JSON.stringify(queryHistory.value))
  } catch (e) {
    console.warn('Failed to save query history:', e)
  }
}

// 记录一次查询：去重（相同文本保留最新），并截断到最多 MAX_QUERY_HISTORY 条
const recordQuery = (text) => {
  const trimmed = text.trim()
  if (!trimmed) return
  const filtered = queryHistory.value.filter(item => item.text !== trimmed)
  const record = {
    text: trimmed,
    date: getTodayKey(),
    timestamp: Date.now()
  }
  queryHistory.value = [record, ...filtered].slice(0, MAX_QUERY_HISTORY)
  saveQueryHistory()
}

// 恢复“当天最后一次查询”：取 date 为今天、timestamp 最新的那条回填输入框
const restoreTodayLastQuery = () => {
  const today = getTodayKey()
  const todayQueries = queryHistory.value.filter(item => item.date === today)
  if (todayQueries.length > 0) {
    const last = todayQueries.reduce((a, b) => (b.timestamp > a.timestamp ? b : a))
    stockInput.value = last.text
  }
}

// 点击历史条目，回填输入框（不自动查询，便于用户确认后再点查询）
const applyHistoryQuery = (item) => {
  stockInput.value = item.text
}

// 移除单条历史
const removeHistoryQuery = (item) => {
  queryHistory.value = queryHistory.value.filter(i => i !== item)
  saveQueryHistory()
}

// 清空全部历史
const clearQueryHistory = () => {
  queryHistory.value = []
  saveQueryHistory()
}

// 压缩多行/超长查询文本用于标签展示（完整内容保留在 title 提示里）
const shortQueryText = (text) => {
  const compact = (text || '').split(/[,，\n\t]/).map(s => s.trim()).filter(Boolean).join(' ')
  return compact.length > 30 ? compact.slice(0, 30) + '…' : compact
}

// 分页处理
const handlePageChange = (page) => {
  currentPage.value = page
  selectedStockIndex.value = 0 // 重置选中索引到第一个
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

// 解析输入的股票代码
const parsedCodes = computed(() => {
  if (!stockInput.value.trim()) return []
  
  const text = stockInput.value
  const separators = [',', '，', '\n', '\t']
  let codes = [text]
  
  for (const sep of separators) {
    const newCodes = []
    for (const code of codes) {
      newCodes.push(...code.split(sep))
    }
    codes = newCodes
  }
  
  return codes.map(c => c.trim()).filter(c => c.length > 0)
})

// 统计信息
const upCount = computed(() => stocks.value.filter(s => s.change_pct > 0).length)
const downCount = computed(() => stocks.value.filter(s => s.change_pct < 0).length)
const flatCount = computed(() => stocks.value.filter(s => s.change_pct === 0).length)

// 行业分布统计：按 industry 分组计数，取前 3 名（忽略缺失/空行业字段的股票）
const topIndustries = computed(() => {
  const counts = {}
  for (const s of stocks.value) {
    const ind = s.industry
    if (!ind) continue
    counts[ind] = (counts[ind] || 0) + 1
  }
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
    .slice(0, 3)
})

// 数据缓存
const klineDataCache = ref(new Map())
const chartRefs = ref(new Map())

// K线周期：默认日线，可切换周线
const klinePeriod = ref('daily')

// 返回指定股票的K线数据（缓存值形如 { period, data }，此处仅暴露数据数组）
const getKlineData = (tsCode) => klineDataCache.value.get(tsCode)?.data || []

// 周期切换：重新拉取当前所有股票的K线
const handleKlinePeriodChange = () => {
  if (stocks.value.length === 0) return
  stocks.value.forEach(stock => {
    fetchKlineData(stock.ts_code)
  })
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

// 获取板块股票列表
const fetchSectorStocks = async () => {
  const sectorCode = route.query.sector
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
      searchQuery.value.trim() || null
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

// 批量获取K线数据（按当前选择的周期，缓存值带 period 以区分不同周期）
const fetchKlineData = async (tsCode) => {
  const cached = klineDataCache.value.get(tsCode)
  if (cached && cached.period === klinePeriod.value) return

  const period = klinePeriod.value
  try {
    const response = await realtimeApi.getKline(tsCode, period, 180)
    if (response.success && response.data && response.data.data) {
      // 若请求期间周期已被切换，则丢弃旧周期的响应，避免覆盖新数据
      if (klinePeriod.value !== period) return
      // 使用前复权处理K线价格，消除送股、配股、分红等事件的影响
      const adjustedData = forwardAdjustKlineData(response.data.data)
      klineDataCache.value.set(tsCode, { period, data: adjustedData })
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

// 获取实时价格
const fetchPrices = async () => {
  if (isSectorMode.value) {
    await fetchSectorStocks()
    return
  }

  if (!stockInput.value.trim()) {
    ElMessage.warning('请输入股票代码')
    return
  }

  loading.value = true
  hasSearched.value = true

  // 清理旧的数据缓存
  klineDataCache.value.clear()

  try {
    const response = await realtimeApi.getPrices(stockInput.value)
    if (response.success) {
      // 记录本次查询到历史缓存（页面刷新时恢复当天最后一次查询）
      recordQuery(stockInput.value)

      // 按照输入顺序排序股票列表
      const stockData = response.data || []
      const codeOrder = new Map(parsedCodes.value.map((code, index) => [code, index]))
      stocks.value = stockData.sort((a, b) => {
        const orderA = codeOrder.get(a.ts_code) ?? 999999
        const orderB = codeOrder.get(b.ts_code) ?? 999999
        return orderA - orderB
      })
      if (stocks.value.length === 0) {
        ElMessage.info('未找到股票数据，请检查代码是否正确')
      } else {
        ElMessage.success(`成功获取 ${stocks.value.length} 只股票数据`)
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
    console.error('Failed to fetch prices:', error)
    ElMessage.error('获取实时价格失败：' + (error.response?.data?.detail || error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

// 监听路由参数变化
watch(() => route.query.sector, (newSector) => {
  if (newSector) {
    fetchSectorStocks()
  } else {
    stocks.value = []
    sectorInfo.value = null
    searchQuery.value = ''
    currentPage.value = 1
  }
  selectedStockIndex.value = 0
}, { immediate: true })

// 页面加载时检查路由参数
onMounted(() => {
  loadQueryHistory()
  if (route.query.sector) {
    fetchSectorStocks()
  } else {
    // 非板块模式：恢复当天最后一次查询的输入
    restoreTodayLastQuery()
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
  addToWatchlist
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
.realtime-price-page {
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
  background: var(--stock-up-glow);
}

.sector-change.down {
  color: var(--stock-down);
  background: var(--stock-down-glow);
}

.sector-change.flat {
  color: var(--text-muted);
  background: var(--bg-hover);
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
  position: sticky;
  top: 20px;
  z-index: 100;
}

.filter-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.search-info {
  margin-top: 10px;
}

.input-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-header .options-label {
  margin-right: 4px;
}

.input-actions {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-top: 15px;
  gap: 15px;
}

.input-actions .parsed-info {
  margin-left: auto;
}

.parsed-info {
  font-size: 14px;
  color: var(--stock-down);
}

/* 最近查询历史 */
.history-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
}

.history-label {
  font-size: 13px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.history-tag {
  cursor: pointer;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-tag .el-tag__content {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-clear {
  margin-left: auto;
  flex-shrink: 0;
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
  color: var(--text-muted);
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

/* 行业分布统计卡片 */
.industry-stats-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.industry-stats-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}

.industry-stats-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.industry-stats-subtitle {
  font-size: 12px;
  color: var(--text-muted);
}

.industry-stats-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.industry-stats-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.industry-stats-name {
  flex: 0 0 96px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.industry-stats-bar-track {
  flex: 1;
  height: 8px;
  background: var(--bg-input);
  border-radius: 4px;
  overflow: hidden;
}

.industry-stats-bar {
  height: 100%;
  background: var(--accent);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.industry-stats-count {
  flex-shrink: 0;
  font-weight: 600;
}

.stocks-container {
  min-height: 200px;
}

/* K线周期选择栏 */
.chart-options-bar {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 12px;
}

.chart-options {
  display: flex;
  align-items: center;
  gap: 10px;
}

.options-label {
  font-size: 13px;
  color: var(--text-muted);
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

.market-tag {
  margin-top: 6px;
  margin-left: 4px;
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
  .realtime-price-page {
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

  .input-actions {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }

  .parsed-info {
    text-align: center;
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

  .price-details,
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
