<template>
  <div class="page-container">

    <el-card class="filter-card">
      <el-form :inline="true">
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
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="tableData" stripe border @sort-change="handleSortChange" @row-click="handleRowClick" :row-class-name="tableRowClassName">
        <el-table-column prop="ts_code" label="TS代码" width="130" fixed="left">
          <template #default="{ row }">
            <a :href="`/stock/${row.ts_code}`" target="_blank" rel="noopener" style="color: var(--el-color-primary); text-decoration: none;">
              {{ row.ts_code }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="stock_name" label="股票名称" width="120" fixed="left" />
        <el-table-column prop="industry" label="板块" width="140" />
        <el-table-column prop="signal_date" label="信号日期" width="120" sortable="custom" />
        <el-table-column label="T+1 涨幅" width="100" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row['change_T+1'])">{{ formatPct(row['change_T+1']) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="T+2 涨幅" width="100" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row['change_T+2'])">{{ formatPct(row['change_T+2']) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="T+3 涨幅" width="100" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row['change_T+3'])">{{ formatPct(row['change_T+3']) }}</span>
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
import { signalApi, realtimeApi } from '@/api'

const loading = ref(false)
const tableData = ref([])

// 行选中相关
const selectedRowId = ref(null)

const filter = reactive({
  signalDate: null,
  dateRange: null
})

const pagination = reactive({
  page: 1,
  page_size: 30,
  total: 0,
  total_pages: 0
})

const fetchTrendData = async (buyPoints) => {
  if (!buyPoints || !buyPoints.length) return

  // Group by signal_date
  const dateGroups = {}
  for (const bp of buyPoints) {
    if (!bp.signal_date || !bp.ts_code) continue
    if (!dateGroups[bp.signal_date]) {
      dateGroups[bp.signal_date] = []
    }
    dateGroups[bp.signal_date].push(bp.ts_code)
  }

  // For each date group, call queryByDate with days=[1,2,3]
  const trendMap = {} // key: ts_code + '_' + signal_date
  const promises = Object.entries(dateGroups).map(async ([date, codes]) => {
    // Deduplicate codes
    const uniqueCodes = [...new Set(codes)]
    try {
      const result = await realtimeApi.queryByDate(uniqueCodes, date, [1, 2, 3])
      if (result.data) {
        for (const item of result.data) {
          trendMap[item.ts_code + '_' + date] = item
        }
      }
    } catch (err) {
      console.error(`Failed to fetch trend data for ${date}:`, err)
    }
  })

  await Promise.all(promises)

  // Merge trend data into tableData
  for (const row of tableData.value) {
    const key = row.ts_code + '_' + row.signal_date
    const trend = trendMap[key]
    if (trend) {
      row['change_T+1'] = trend['change_T+1'] ?? null
      row['change_T+2'] = trend['change_T+2'] ?? null
      row['change_T+3'] = trend['change_T+3'] ?? null
      row['close_T+0'] = trend['close_T+0'] ?? null
    }
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      signal_date: filter.signalDate || null,
      signal_date_start: filter.dateRange ? filter.dateRange[0] : null,
      signal_date_end: filter.dateRange ? filter.dateRange[1] : null
    }
    const res = await signalApi.getBuyPoints(params)
    if (res.success) {
      tableData.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total
        pagination.total_pages = res.pagination.total_pages
      }
      // Fetch T+1/T+2/T+3 trend data
      await fetchTrendData(tableData.value)
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
  filter.signalDate = null
  filter.dateRange = null
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

const openXueqiu = (tsCode) => {
  if (!tsCode) return
  const [code, exchange] = tsCode.split('.')
  const xueqiuCode = exchange + code
  window.open(`https://xueqiu.com/S/${xueqiuCode}`, '_blank')
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

onMounted(() => {
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
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.up {
  color: #f56c6c;
}
.down {
  color: #67c23a;
}
.flat {
  color: #909399;
}

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
</style>
