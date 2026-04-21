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
          <span>股票输入</span>
          <el-tag type="info" size="small">支持股票代码或名称，一行一个</el-tag>
        </div>
      </template>

      <el-input
        v-model="stockInput"
        type="textarea"
        :rows="4"
        placeholder="请输入股票代码或名称，如：&#10;600000.SH&#10;000001.SZ&#10;或&#10;平安银行&#10;贵州茅台"
        :disabled="loading"
      />

      <div class="input-actions">
        <div class="parsed-info" v-if="parsedCodes.length > 0">
          <el-tag type="success">已解析 {{ parsedCodes.length }} 个</el-tag>
        </div>
        <el-button
          type="primary"
          @click="fetchPrices"
          :loading="loading"
          :disabled="!stockInput.trim()"
        >
          查询实时价格
        </el-button>
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

    <!-- 股票列表 -->
    <div v-loading="loading" class="stocks-container">
      <el-empty v-if="!loading && stocks.length === 0 && hasSearched" description="暂无数据" />
      
      <div v-if="stocks.length > 0" class="stock-list">
        <div 
          v-for="stock in stocks" 
          :key="stock.ts_code"
          class="stock-card" 
          :class="getChangeClass(stock.change_pct)"
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
              
              <!-- 价格详情 -->
              <div class="price-details">
                <div class="detail-row">
                  <span class="label">昨收</span>
                  <span class="value">¥{{ (stock.pre_close ?? 0).toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">今开</span>
                  <span class="value">¥{{ (stock.open ?? 0).toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">最高</span>
                  <span class="value up">¥{{ (stock.high ?? 0).toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">最低</span>
                  <span class="value down">¥{{ (stock.low ?? 0).toFixed(2) }}</span>
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
              <el-button size="small" @click="viewDetail(stock)">
                <el-icon><View /></el-icon>详情
              </el-button>
              <el-button
                size="small"
                type="warning"
                @click="addToWatchlist(stock)"
                :loading="stock.addingToWatchlist"
                :disabled="stock.isWatched"
              >
                <el-icon><Star /></el-icon>{{ stock.isWatched ? '已关注' : '关注' }}
              </el-button>
              <el-button size="small" type="primary" link @click="openXueqiu(stock)">
                雪球
              </el-button>
            </div>
          </div>
          
          <!-- 右侧：K线图 -->
          <div class="stock-chart-section">
            <StockKlineChart
              :ref="(el) => { if (el) chartRefs.set(stock.ts_code, el) }"
              :ts-code="stock.ts_code"
              :stock-name="stock.name"
              :kline-data="klineDataCache.get(stock.ts_code) || []"
              :show-m-a-c-d="true"
              min-height="260px"
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
import { Refresh, View, ArrowLeft, Search, Star } from '@element-plus/icons-vue'
import { realtimeApi, watchlistApi } from '@/api'
import api from '@/api'
import StockKlineChart from '@/components/StockKlineChart.vue'
import FollowStockDialog from '@/components/FollowStockDialog.vue'

const router = useRouter()
const route = useRoute()

// 判断是否为板块模式
const isSectorMode = computed(() => !!route.query.sector)

// 页面标题
const pageTitle = computed(() => {
  if (isSectorMode.value) {
    return route.query.sectorName ? `${route.query.sectorName} - 板块股票` : '板块股票'
  }
  return '实时股价'
})

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

// 返回板块列表
const goBack = () => {
  router.push('/sectors')
}

// 分页处理
const handlePageChange = (page) => {
  currentPage.value = page
  fetchSectorStocks()
}

const handleSizeChange = (size) => {
  // 固定每页20条，不再需要切换页面大小
  console.warn('handleSizeChange is deprecated, page size is fixed at 20')
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
  const sectorCode = route.query.sector
  const sectorType = route.query.sectorType || 'industry'

  if (!sectorCode) return

  loading.value = true
  hasSearched.value = true

  // 清理旧的数据缓存
  klineDataCache.value.clear()

  try {
    // 获取板块详情和股票列表（后端分页）
    const response = await api.get(`/sectors/${sectorCode}/stocks`, {
      params: {
        sector_type: sectorType,
        page: currentPage.value,
        page_size: 20, // 固定每页20条
        search: searchQuery.value.trim() || undefined
      }
    })

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
    ElMessage.error('获取板块股票失败：' + (error.message || '网络错误'))
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
    ElMessage.error('获取实时价格失败：' + (error.message || '网络错误'))
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
}, { immediate: true })

// 页面加载时检查路由参数
onMounted(() => {
  if (route.query.sector) {
    fetchSectorStocks()
  }
})

// 涨跌幅样式
const getChangeClass = (changePct) => {
  if (changePct > 0) return 'up'
  if (changePct < 0) return 'down'
  return 'flat'
}

// 格式化涨跌幅显示
const formatChange = (changePct) => {
  if (changePct > 0) return `+${changePct.toFixed(2)}%`
  if (changePct < 0) return `${changePct.toFixed(2)}%`
  return '0.00%'
}

// 格式化成交量
const formatVolume = (volume) => {
  if (!volume) return '-'
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  }
  return volume.toString()
}

// 格式化成交额
const formatAmount = (amount) => {
  if (!amount) return '-'
  amount = amount * 1000
  if (amount >= 100000000) {
    return '¥' + (amount / 100000000).toFixed(2) + '亿'
  } else if (amount >= 10000) {
    return '¥' + (amount / 10000).toFixed(2) + '万'
  }
  return '¥' + amount.toFixed(0)
}

// 查看详情
const viewDetail = (stock) => {
  if (!stock.ts_code) return
  window.open(`/stock/${stock.ts_code}`, '_blank')
}

// 打开雪球网
const openXueqiu = (stock) => {
  // 转换格式: 300006.SZ -> SZ300006
  const [code, exchange] = stock.ts_code.split('.')
  const xueqiuCode = exchange + code
  window.open(`https://xueqiu.com/S/${xueqiuCode}`, '_blank')
}

// 添加到关注列表
const addToWatchlist = (stock) => {
  openFollowDialog(stock)
}

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
  color: #303133;
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
  color: #303133;
}

.sector-change {
  font-size: 24px;
  font-weight: 700;
  padding: 8px 16px;
  border-radius: 8px;
}

.sector-change.up {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.sector-change.down {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}

.sector-change.flat {
  color: #909399;
  background: rgba(144, 147, 153, 0.1);
}

.sector-stats {
  display: flex;
  gap: 30px;
  color: #606266;
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

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
}

.parsed-info {
  font-size: 14px;
  color: #67c23a;
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
  color: #409eff;
  margin-bottom: 5px;
}

.stat-card.up .stat-value {
  color: #f56c6c;
}

.stat-card.down .stat-value {
  color: #67c23a;
}

.stat-card.flat .stat-value {
  color: #909399;
}

.stat-label {
  font-size: 14px;
  color: #909399;
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
  background: #fff;
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
  border-color: #f56c6c;
}

.stock-card.down {
  border-color: #67c23a;
}

.stock-card.flat {
  border-color: #dcdfe6;
}

/* 左侧信息区域 */
.stock-info-section {
  flex: 0 0 320px;
  padding: 20px;
  background: #fafbfc;
  border-right: 1px solid #ebeef5;
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
  color: #303133;
  margin-bottom: 4px;
}

.stock-code {
  font-size: 13px;
  color: #909399;
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
  color: white;
}

.change-badge.up {
  background: linear-gradient(135deg, #f56c6c 0%, #ff8c8c 100%);
}

.change-badge.down {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.change-badge.flat {
  background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
}

.stock-body {
  flex: 1;
}

.price-section {
  text-align: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.current-price {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 6px;
}

.current-price.up {
  color: #f56c6c;
}

.current-price.down {
  color: #67c23a;
}

.current-price.flat {
  color: #909399;
}

.change-info {
  font-size: 13px;
}

.change-info .up {
  color: #f56c6c;
}

.change-info .down {
  color: #67c23a;
}

.change-info .flat {
  color: #909399;
}

.price-details {
  background-color: #fff;
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
  color: #909399;
}

.detail-row .value {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.detail-row .value.up {
  color: #f56c6c;
}

.detail-row .value.down {
  color: #67c23a;
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
  color: #909399;
}

.volume-row .value {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.bid-ask-section {
  background-color: #fff;
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
  color: #67c23a;
  font-size: 11px;
  font-weight: 600;
}

.ask .label {
  color: #f56c6c;
  font-size: 11px;
  font-weight: 600;
}

.bid .value, .ask .value {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.bid .volume, .ask .volume {
  font-size: 11px;
  color: #909399;
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

.trade-time {
  margin-left: 8px;
  color: #409eff;
}

.stock-footer {
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

/* 右侧图表区域 */
.stock-chart-section {
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
    border-bottom: 1px solid #ebeef5;
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
