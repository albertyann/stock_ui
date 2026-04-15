<template>
  <div class="page-container">
    <div class="page-header">
      <h2>日线数据</h2>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="股票名称">
          <el-input
            v-model="filter.name"
            placeholder="输入股票名称"
            clearable
            @keyup.enter="handleFilterChange"
            @clear="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="TS代码">
          <el-input
            v-model="filter.ts_code"
            placeholder="输入ts_code"
            clearable
            @keyup.enter="handleFilterChange"
            @clear="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="交易日期">
          <el-date-picker
            v-model="filter.trade_date"
            type="date"
            placeholder="选择日期"
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
        <el-table-column prop="ts_code" label="TS代码" width="130" />
        <el-table-column prop="name" label="股票名称" width="120" />
        <el-table-column prop="trade_date" label="交易日期" width="120" />
        <el-table-column prop="open" label="开盘价" width="100" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.open) }}
          </template>
        </el-table-column>
        <el-table-column prop="high" label="最高价" width="100" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.high) }}
          </template>
        </el-table-column>
        <el-table-column prop="low" label="最低价" width="100" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.low) }}
          </template>
        </el-table-column>
        <el-table-column prop="close" label="收盘价" width="100" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.close) }}
          </template>
        </el-table-column>
        <el-table-column prop="pre_close" label="昨收价" width="100" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.pre_close) }}
          </template>
        </el-table-column>
        <el-table-column prop="change" label="涨跌额" width="100" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row.change)">{{ formatPrice(row.change) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pct_chg" label="涨跌幅" width="100" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row.pct_chg)">{{ formatPct(row.pct_chg) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="vol" label="成交量" width="120" align="right">
          <template #default="{ row }">
            {{ formatVolume(row.vol) }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="成交额" width="140" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.amount) }}
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
import { ElMessage } from 'element-plus'
import { basicDataApi } from '@/api'

const loading = ref(false)
const tableData = ref([])

const filter = reactive({
  name: '',
  ts_code: '',
  trade_date: ''
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
    const res = await basicDataApi.getDailyData({
      page: pagination.page,
      page_size: pagination.page_size,
      name: filter.name || null,
      ts_code: filter.ts_code || null,
      trade_date: filter.trade_date || null
    })
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
  filter.name = ''
  filter.ts_code = ''
  filter.trade_date = ''
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

const formatPrice = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(2)
}

const formatPct = (val) => {
  if (val === null || val === undefined) return '-'
  const num = Number(val)
  return (num > 0 ? '+' : '') + num.toFixed(2) + '%'
}

const getChangeClass = (val) => {
  if (val === null || val === undefined) return ''
  const num = Number(val)
  return num > 0 ? 'up' : num < 0 ? 'down' : ''
}

const formatVolume = (val) => {
  if (val === null || val === undefined) return '-'
  const num = Number(val)
  if (num >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿'
  }
  if (num >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(0)
}

const formatAmount = (val) => {
  if (val === null || val === undefined) return '-'
  const num = Number(val)
  if (num >= 100000000) {
    return '¥' + (num / 100000000).toFixed(2) + '亿'
  }
  if (num >= 10000) {
    return '¥' + (num / 10000).toFixed(2) + '万'
  }
  return '¥' + num.toFixed(2)
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
.up {
  color: #f56c6c;
}
.down {
  color: #67c23a;
}
</style>
