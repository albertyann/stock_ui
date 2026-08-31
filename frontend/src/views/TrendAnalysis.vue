<template>
  <div class="page-container">

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="策略">
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
        <el-form-item label="板块">
          <el-select
            v-model="filter.industry"
            placeholder="全部板块"
            clearable
            style="width: 160px"
            @change="handleFilterChange"
          >
            <el-option
              v-for="i in meta.industries"
              :key="i"
              :label="i"
              :value="i"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="信号日期">
          <el-date-picker
            v-model="filter.signalDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            clearable
            @change="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filter.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            clearable
            @change="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="数据范围">
          <el-switch
            v-model="filter.isAll"
            :active-text="'全部'"
            :inactive-text="'近5天'"
            inline-prompt
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
        <el-form-item label="观察天数">
          <el-checkbox-group v-model="filter.days" @change="handleFilterChange">
            <el-checkbox v-for="d in dayOptions" :key="d" :label="d" :value="d">
              {{ d }}天
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <div class="table-toolbar" v-if="filter.days.length">
        <el-radio-group v-model="metricMode" size="small">
          <el-radio-button label="当天涨幅" value="change" />
          <el-radio-button label="累计涨幅" value="cumulative" />
        </el-radio-group>
      </div>
      <el-table :data="tableData" stripe border @sort-change="handleSortChange" @row-click="handleRowClick" :row-class-name="tableRowClassName">
        <el-table-column prop="ts_code" label="TS代码" width="130" fixed="left">
          <template #default="{ row }">
            <a :href="`/stock/${row.ts_code}`" target="_blank" rel="noopener" style="color: var(--el-color-primary); text-decoration: none;">
              {{ row.ts_code }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="股票名称" width="120" fixed="left" />
        <el-table-column prop="industry" label="板块" width="140" />
        <el-table-column prop="board_type" label="市场" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getBoardType(row.ts_code).type">
              {{ getBoardType(row.ts_code).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strategy_name" label="策略" width="160" />
        <el-table-column prop="score" label="评分" width="90" align="right">
          <template #default="{ row }">
            {{ row.score === null || row.score === undefined ? '-' : Number(row.score).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="signal_date" label="信号日期" width="120" sortable="custom" />
        <el-table-column prop="close_T+0" label="T日收盘" width="100" align="right">
          <template #default="{ row }">
            {{ row['close_T+0'] === null || row['close_T+0'] === undefined ? '-' : Number(row['close_T+0']).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column
          v-for="day in filter.days"
          :key="day"
          :label="'T+' + day + ' 涨幅'"
          width="100"
          align="right"
          sortable="custom"
        >
          <template #header="{ column }">
            <el-tooltip
              v-if="getDayTradingDate(day)"
              :content="getDayTradingDate(day)"
              placement="top"
            >
              <span>{{ column.label }}</span>
            </el-tooltip>
            <span v-else>{{ column.label }}</span>
          </template>
          <template #default="{ row }">
            <span :class="getChangeClass(metricMode === 'change' ? row['change_T+' + day] : row['cumulative_change_T+' + day])">
              {{ formatPct(metricMode === 'change' ? row['change_T+' + day] : row['cumulative_change_T+' + day]) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="openStockDetail(row.ts_code)">
              详情
            </el-button>
            <el-button type="primary" size="small" link @click="openXueqiu(row.ts_code)">
              雪球
            </el-button>
          </template>
        </el-table-column>
      </el-table>

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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { trendApi, screeningApi } from '@/api'
import { openXueqiu } from '@/utils/stock'

const loading = ref(false)
const tableData = ref([])

// 行选中相关
const selectedRowId = ref(null)

// 涨幅口径: change = 当天涨幅, cumulative = 累计涨幅
const metricMode = ref('cumulative')

const dayOptions = [1, 2, 3, 4, 5]

const filter = reactive({
  strategy_name: null,
  industry: null,
  signalDate: null,
  dateRange: null,
  isAll: false,
  market_type: 'chye',
  days: [1, 2, 3, 4, 5]
})

const pagination = reactive({
  page: 1,
  page_size: 30,
  total: 0,
  total_pages: 0
})

const meta = reactive({
  strategies: [],
  industries: []
})

// 各信号日期对应的 T+N 实际交易日: { '2026-08-13': { 'T+0': '2026-08-13', 'T+1': '2026-08-14' } }
const tradingDates = ref({})

const getRecent5DaysStart = () => {
  const now = new Date()
  now.setDate(now.getDate() - 5)
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// 返回当前列 (T+day) 对应的实际交易日，供表头 tooltip 展示
// 优先取第一条有该日期映射的行的 signal_date
const getDayTradingDate = (day) => {
  for (const row of tableData.value) {
    const dates = tradingDates.value[row.signal_date]
    if (dates && dates['T+' + day]) {
      return dates['T+' + day]
    }
  }
  return null
}

const fetchMeta = async () => {
  try {
    const res = await screeningApi.getResultsMeta()
    if (res.data) {
      meta.strategies = res.data.strategies || []
      meta.industries = res.data.industries || []
    }
  } catch (err) {
    console.error('Failed to fetch meta:', err)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    let dateStart = filter.dateRange ? filter.dateRange[0] : null
    let dateEnd = filter.dateRange ? filter.dateRange[1] : null

    if (!filter.isAll) {
      // Force recent 5 days
      dateStart = getRecent5DaysStart()
      dateEnd = null
    }

    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      strategy_name: filter.strategy_name || null,
      industry: filter.industry || null,
      signal_date: filter.signalDate || null,
      date_start: dateStart,
      date_end: dateEnd,
      market_type: filter.market_type || null,
      min_score: null,
      days: filter.days
    }
    const res = await trendApi.getTrends(params)
    if (res.success) {
      tableData.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total
        pagination.total_pages = res.pagination.total_pages
      }
      tradingDates.value = res.trading_dates || {}
    } else {
      ElMessage.error(res.error || '获取数据失败')
    }
  } catch (err) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

const resetFilter = () => {
  filter.strategy_name = null
  filter.industry = null
  filter.signalDate = null
  filter.dateRange = null
  filter.isAll = false
  filter.market_type = 'chye'
  filter.days = [1, 2, 3, 4, 5]
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

const handleSortChange = () => {
  pagination.page = 1
  fetchData()
}

const handleRowClick = (row) => {
  selectedRowId.value = row.ts_code
}

const tableRowClassName = ({ row }) => {
  if (row.ts_code === selectedRowId.value) {
    return 'selected-row'
  }
  return ''
}

const openStockDetail = (tsCode) => {
  if (!tsCode) return
  window.open(`/stock/${tsCode}`, '_blank')
}

const formatPct = (pct) => {
  if (pct === null || pct === undefined) return '-'
  const val = Number(pct)
  return (val > 0 ? '+' : '') + val.toFixed(2) + '%'
}

const getChangeClass = (val) => {
  if (val === null || val === undefined) return ''
  if (val > 0) return 'up'
  if (val < 0) return 'down'
  return 'flat'
}

const getBoardType = (tsCode) => {
  if (!tsCode) return { label: '', type: 'info' }
  const code = tsCode.split('.')[0]
  const prefix = code.substring(0, 3)
  // 科创板
  if (['688', '689'].includes(prefix)) {
    return { label: '科创板', type: 'warning' }
  }
  // 创业板
  if (['300', '301'].includes(prefix)) {
    return { label: '创业板', type: 'success' }
  }
  // 北交所
  if (prefix.startsWith('8') || ['430', '831', '832', '833', '834', '835', '836', '837', '838', '839', '870', '871', '872', '873'].includes(prefix)) {
    return { label: '北交所', type: 'danger' }
  }
  // 主板
  return { label: '主板', type: 'info' }
}

onMounted(() => {
  fetchMeta()
  fetchData()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.filter-card {
  margin-bottom: 20px;
}
.table-toolbar {
  margin-bottom: 12px;
  display: flex;
  justify-content: flex-end;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.up {
  color: var(--stock-up);
}
.down {
  color: var(--stock-down);
}
.flat {
  color: var(--text-muted);
}

/* 修复 fixed(sticky) 列背景透明：横向滚动时下层内容会透出。
   正常行用不透明卡片背景覆盖；不加 !important，
   让全局斑马纹/悬停的 !important 规则继续作用于 fixed 单元格 */
:deep(.el-table .el-table__body td.el-table-fixed-column--left),
:deep(.el-table .el-table__body td.el-table-fixed-column--right) {
  background-color: var(--bg-card-solid);
}

:deep(.el-table .selected-row > td.el-table__cell) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table .el-table__fixed .selected-row > td.el-table__cell) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table .el-table__fixed-right .selected-row > td.el-table__cell) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: var(--bg-active) !important;
}

:deep(.el-table .el-table__fixed .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: var(--bg-active) !important;
}

:deep(.el-table .el-table__fixed-right .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: var(--bg-active) !important;
}
</style>
