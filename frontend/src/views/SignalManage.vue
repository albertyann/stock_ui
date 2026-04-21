<template>
  <div class="page-container">
    <div class="page-header">
      <h2>信号管理</h2>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="股票代码">
          <el-input
            v-model="filter.ts_code"
            placeholder="输入ts_code"
            clearable
            @keyup.enter="handleFilterChange"
            @clear="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="信号类型">
          <el-select
            v-model="filter.signal_type"
            placeholder="全部"
            clearable
            @change="handleFilterChange"
          >
            <el-option label="买入 (BUY)" value="BUY" />
            <el-option label="卖出 (SELL)" value="SELL" />
            <el-option label="观察 (WATCH)" value="WATCH" />
            <el-option label="备注 (NOTE)" value="NOTE" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filter.is_active"
            placeholder="全部"
            clearable
            @change="handleFilterChange"
          >
            <el-option label="活跃" :value="true" />
            <el-option label="已关闭" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="信号日期">
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
          <el-button type="primary" @click="handleFilterChange">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="tableData" stripe border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="ts_code" label="股票代码" width="130" />
        <el-table-column prop="signal_type" label="信号类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getSignalTagType(row.signal_type)">
              {{ getSignalLabel(row.signal_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="signal_strength" label="信号强度" width="100">
          <template #default="{ row }">
            {{ formatStrength(row.signal_strength) }}
          </template>
        </el-table-column>
        <el-table-column prop="signal_date" label="信号日期" width="120" />
        <el-table-column prop="note_content" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { signalApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])

const filter = reactive({
  ts_code: '',
  signal_type: null,
  is_active: null,
  dateRange: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ts_code: filter.ts_code || null,
      signal_type: filter.signal_type || null,
      is_active: filter.is_active !== null && filter.is_active !== undefined ? filter.is_active : null,
      signal_date_start: filter.dateRange ? filter.dateRange[0] : null,
      signal_date_end: filter.dateRange ? filter.dateRange[1] : null
    }
    const res = await signalApi.getSignalsManage(params)
    if (res.success) {
      tableData.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total
        pagination.total_pages = res.pagination.total_pages
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

const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

const resetFilter = () => {
  filter.ts_code = ''
  filter.signal_type = null
  filter.is_active = null
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

const handleView = (row) => {
  router.push(`/stock/${row.ts_code}`)
}

const formatPrice = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(2)
}

const formatStrength = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(1)
}

const getSignalTagType = (type) => {
  const map = { BUY: 'danger', SELL: 'success', WATCH: 'warning', NOTE: 'info' }
  return map[type] || ''
}

const getSignalLabel = (type) => {
  const map = { BUY: '买入', SELL: '卖出', WATCH: '观察', NOTE: '备注' }
  return map[type] || type
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}
.filter-card {
  margin-bottom: 20px;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
