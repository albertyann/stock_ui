<template>
  <div class="concept-detail-page">
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

        <el-table
          :data="displayStocks"
          style="width: 100%"
          stripe
          border
          :row-class-name="getRowClassName"
          @row-click="handleRowClick"
          highlight-current-row
        >
          <el-table-column label="股票代码" width="130" fixed="left">
            <template #default="{ row }">
              <a
                :href="`/stock/${row.ts_code}`"
                target="_blank"
                class="stock-link"
                @click.stop="selectRow(row)"
              >
                {{ row.ts_code }}
              </a>
            </template>
          </el-table-column>

          <el-table-column prop="name" label="名称" width="100" fixed="left" />

          <el-table-column label="最新价" width="100" align="right">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_pct)">
                ¥{{ (row.price ?? 0).toFixed(2) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="涨跌幅" width="110" align="right">
            <template #header>
              <span @click.stop="toggleChangeSort" style="cursor: pointer; display: inline-flex; align-items: center; gap: 2px;">
                涨跌幅
                <el-icon v-if="sortOrder === 'desc'" style="color: #f56c6c;"><ArrowDown /></el-icon>
                <el-icon v-else-if="sortOrder === 'asc'" style="color: #67c23a;"><ArrowUp /></el-icon>
                <el-icon v-else style="color: #c0c4cc;"><Sort /></el-icon>
              </span>
            </template>
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_pct)">
                {{ formatChange(row.change_pct) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="涨跌额" width="100" align="right">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_pct)">
                {{ (row.change ?? 0) >= 0 ? '+' : '' }}{{ (row.change ?? 0).toFixed(2) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="成交量" width="120" align="right">
            <template #default="{ row }">
              {{ formatVolume(row.volume) }}
            </template>
          </el-table-column>

          <el-table-column label="成交额" width="130" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.amount) }}
            </template>
          </el-table-column>


          <el-table-column label="更新时间" width="160">
            <template #default="{ row }">
              <div class="time-cell">
                <div>{{ row.update_time }}</div>
                <div v-if="row.trade_time" class="trade-time-small">{{ row.trade_time }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                type="warning"
                @click.stop="addToWatchlist(row)"
                :loading="row.addingToWatchlist"
                :disabled="row.isWatched"
              >
                {{ row.isWatched ? '已关注' : '关注' }}
              </el-button>
              <el-button size="small" type="primary" link @click.stop="viewDetail(row)">
                详情
              </el-button>
              <el-button size="small" type="primary" link @click.stop="openXueqiu(row)">
                雪球
              </el-button>
            </template>
          </el-table-column>
        </el-table>

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
import { ref, computed, onUnmounted, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowUp, ArrowDown, Sort, Search } from '@element-plus/icons-vue'
import { watchlistApi, sectorApi } from '@/api'
import FollowStockDialog from '@/components/FollowStockDialog.vue'

const router = useRouter()
const route = useRoute()

// 选中股票（用于表格高亮和键盘导航）
const selectedRow = ref(null)
const selectedStockIndex = ref(0)

// Ctrl+x 前缀键状态
const ctrlXPressed = ref(false)

// 表格行点击选中
const selectRow = (row) => {
  selectedRow.value = row
  const index = displayStocks.value.findIndex(item => item.ts_code === row.ts_code)
  if (index !== -1) {
    selectedStockIndex.value = index
  }
}

const handleRowClick = (row) => {
  selectRow(row)
}

const getRowClassName = ({ row }) => {
  if (selectedRow.value && row.ts_code === selectedRow.value.ts_code) {
    return 'selected-row'
  }
  return ''
}

// 按涨跌幅排序
const sortByChangePct = (a, b) => {
  return (a.change_pct || 0) - (b.change_pct || 0)
}

// 点击涨跌幅列头切换后端全局排序: default → desc → asc → default
const toggleChangeSort = () => {
  const cycle = { default: 'desc', desc: 'asc', asc: 'default' }
  sortOrder.value = cycle[sortOrder.value] || 'default'
  handleSortChange()
}

// 键盘事件处理
const handleKeydown = (event) => {
  // 如果焦点在输入框或文本框中，不处理快捷键
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.isContentEditable) {
    return
  }

  const maxIndex = displayStocks.value.length - 1

  // 处理 Ctrl+x 前缀键
  if (event.ctrlKey && event.key === 'x') {
    event.preventDefault()
    ctrlXPressed.value = true
    return
  }

  // 处理 Ctrl+x 后的子命令
  if (ctrlXPressed.value) {
    ctrlXPressed.value = false
    
    if (event.key === 's') {
      // Ctrl+x+s: 关注当前选中的股票
      event.preventDefault()
      const selectedStock = displayStocks.value[selectedStockIndex.value]
      if (selectedStock && !selectedStock.isWatched) {
        addToWatchlist(selectedStock)
      }
      return
    } else if (event.key === 'o') {
      // Ctrl+x+o: 打开雪球
      event.preventDefault()
      const selectedStock = displayStocks.value[selectedStockIndex.value]
      if (selectedStock) {
        openXueqiu(selectedStock)
      }
      return
    }
  }

  // 原有的 j/k 导航
  if (event.key === 'j') {
    event.preventDefault()
    if (selectedStockIndex.value < maxIndex) {
      selectedStockIndex.value++
      const nextStock = displayStocks.value[selectedStockIndex.value]
      if (nextStock) {
        selectRow(nextStock)
      }
    }
  } else if (event.key === 'k') {
    event.preventDefault()
    if (selectedStockIndex.value > 0) {
      selectedStockIndex.value--
      const prevStock = displayStocks.value[selectedStockIndex.value]
      if (prevStock) {
        selectRow(prevStock)
      }
    }
  }

  // h/l 翻页
  const totalPages = Math.ceil(totalStocks.value / pageSize.value)
  if (event.key === 'l') {
    event.preventDefault()
    if (currentPage.value < totalPages) {
      handlePageChange(currentPage.value + 1, true)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  } else if (event.key === 'h') {
    event.preventDefault()
    if (currentPage.value > 1) {
      handlePageChange(currentPage.value - 1, true)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
}

// 页面标题
const pageTitle = computed(() => {
  return route.query.sectorName ? `${route.query.sectorName} - 板块股票` : '板块股票'
})

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
const trendFilter = ref('all') // 'all' | 'up' | 'down'

// 股票列表（后端已按选定规则排序）
const displayStocks = computed(() => {
  return stocks.value
})

// 返回板块列表
const goBack = () => {
  router.push('/concept')
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

// 获取板块股票列表（从 dc_member 表获取板块成分股）
const fetchSectorStocks = async () => {
  const sectorCode = route.query.code
  const tradeDate = route.query.tradeDate || ''

  if (!sectorCode) return

  loading.value = true
  hasSearched.value = true

  try {
    // 使用专用概念板块接口，数据来源为 dc_member 表
    const response = await sectorApi.getConceptSectorStocks(
      sectorCode,
      currentPage.value,
      20,
      searchQuery.value.trim() || null,
      sortOrder.value,
      trendFilter.value !== 'all' ? trendFilter.value : null,
      tradeDate || null
    )

    if (response.success) {
      sectorInfo.value = response.data.sector
      stocks.value = response.data.stocks || []
      totalStocks.value = response.data.pagination?.total || 0

      if (stocks.value.length === 0) {
        ElMessage.info('该板块暂无股票数据（dc_member 表可能无数据）')
      } else {
        ElMessage.success(`成功获取 ${stocks.value.length} 只股票数据（共 ${totalStocks.value} 条）`)
        // 检查关注状态
        checkWatchStatus(stocks.value)
        // 默认选中第一行
        if (stocks.value.length > 0) {
          selectRow(stocks.value[0])
        }
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
    trendFilter.value = 'all'  // keep default as 'all'
  }
  selectedStockIndex.value = 0
}, { immediate: true })

// 页面加载时检查路由参数
onMounted(() => {
  if (route.query.code) {
    fetchSectorStocks()
  }
  // 注册键盘事件监听
  window.addEventListener('keydown', handleKeydown)
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

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.concept-detail-page {
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
}

.filter-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.search-info {
  margin-top: 10px;
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

/* 表格样式 - 与 StockQuery.vue 保持一致 */
.up {
  color: #f56c6c;
}

.down {
  color: #67c23a;
}

.flat {
  color: #909399;
}

.stock-link {
  color: #409eff;
  text-decoration: none;
}

.stock-link:hover {
  text-decoration: underline;
}

/* 选中行高亮 - 与 StockQuery.vue 保持一致 */
:deep(.el-table .selected-row > td.el-table__cell) {
  background-color: #ecf5ff !important;
}

:deep(.el-table .el-table__fixed .selected-row > td.el-table__cell) {
  background-color: #ecf5ff !important;
}

:deep(.el-table .el-table__fixed-right .selected-row > td.el-table__cell) {
  background-color: #ecf5ff !important;
}

:deep(.el-table .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: #d9ecff !important;
}

:deep(.el-table .el-table__fixed .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: #d9ecff !important;
}

:deep(.el-table .el-table__fixed-right .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: #d9ecff !important;
}


/* 时间单元格 */
.time-cell {
  font-size: 13px;
}

.trade-time-small {
  font-size: 12px;
  color: #409eff;
  margin-top: 2px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .concept-detail-page {
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
}
</style>
