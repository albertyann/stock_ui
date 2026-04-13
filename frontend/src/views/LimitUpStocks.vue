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
          v-for="stock in paginatedStocks" 
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
                  ¥{{ stock.price.toFixed(2) }}
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
              
              <!-- 价格详情 -->
              <div class="price-details">
                <div class="detail-row">
                  <span class="label">昨收</span>
                  <span class="value">¥{{ stock.pre_close.toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">今开</span>
                  <span class="value">¥{{ stock.open.toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">最高</span>
                  <span class="value up">¥{{ stock.high.toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">最低</span>
                  <span class="value down">¥{{ stock.low.toFixed(2) }}</span>
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
                <span class="time-value">{{ stock.update_time }}</span>
                <span class="trade-date">
                  交易日：{{ stock.trade_date }}
                </span>
              </div>
            </div>
            
            <div class="stock-footer">
              <el-button size="small" @click="viewDetail(stock)">
                <el-icon><View /></el-icon>详情
              </el-button>
              <el-button size="small" type="warning" @click="addToWatchlist(stock)" :loading="stock.addingToWatchlist">
                <el-icon><Star /></el-icon>关注
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
              :holder-data="holderNumberCache.get(stock.ts_code) || []"
              :show-holder-number="true"
              :show-m-a-c-d="true"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, View, Star, Search } from '@element-plus/icons-vue'
import { realtimeApi, sectorApi } from '@/api'
import api from '@/api'
import StockKlineChart from '@/components/StockKlineChart.vue'

const router = useRouter()

const stocks = ref([])
const loading = ref(false)
const hasLoaded = ref(false)
const tradeDate = ref('')

// 分页相关
const currentPage = ref(1)
const pageSize = ref(50)

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

  // 清理旧的数据缓存
  klineDataCache.value.clear()
  holderNumberCache.value.clear()

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
      klineDataCache.value.set(tsCode, response.data.data)
    }
    
    // 获取股东人数数据
    const holderResponse = await realtimeApi.getHolderNumber(tsCode, 180)
    if (holderResponse.success && holderResponse.data && holderResponse.data.data) {
      holderNumberCache.value.set(tsCode, holderResponse.data.data)
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
  router.push(`/stock/${stock.ts_code}`)
}

// 打开雪球网
const openXueqiu = (stock) => {
  // 转换格式: 300006.SZ -> SZ300006
  const [code, exchange] = stock.ts_code.split('.')
  const xueqiuCode = exchange + code
  window.open(`https://xueqiu.com/S/${xueqiuCode}`, '_blank')
}

// 添加到关注列表
const addToWatchlist = async (stock) => {
  // 设置loading状态
  stock.addingToWatchlist = true
  
  try {
    const response = await api.post('/watchlists/8/stocks', {
      ts_code: stock.ts_code,
      notes: `从涨停股票页面添加 - ${new Date().toLocaleDateString()}`
    })
    
    if (response.success) {
      ElMessage.success(`${stock.name} 已成功加入关注列表`)
    } else {
      ElMessage.warning(response.error || '添加失败，该股票可能已在关注列表中')
    }
  } catch (error) {
    console.error('Failed to add to watchlist:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('添加到关注列表失败：' + (error.message || '网络错误'))
    }
  } finally {
    stock.addingToWatchlist = false
  }
}

// 数据缓存
const klineDataCache = ref(new Map())
const holderNumberCache = ref(new Map())
const chartRefs = ref(new Map())

// 窗口大小变化时重新调整图表
const handleResize = () => {
  chartRefs.value.forEach(chart => {
    chart.resize()
  })
}
window.addEventListener('resize', handleResize)

// 组件挂载时加载数据
fetchLimitUpStocks()
fetchIndustryOptions()

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
  color: #303133;
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
  background-color: #f5f7fa;
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
  color: #606266;
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

.time-section {
  font-size: 11px;
  color: #909399;
  text-align: center;
  margin-bottom: 12px;
}

.time-label {
  margin-right: 4px;
}

.trade-date {
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
  min-height: 420px;
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
