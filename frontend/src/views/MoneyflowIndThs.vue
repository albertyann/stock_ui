<template>
  <div class="moneyflow-ind-ths-page">
    <div class="page-header">
      <h2>行业资金流向</h2>
      <div class="header-actions">
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filter">
        <el-form-item label="交易日期">
          <el-date-picker
            v-model="filter.trade_date"
            type="date"
            placeholder="选择交易日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
            style="width: 160px"
          />
        </el-form-item>
        <el-form-item label="行业名称">
          <el-input
            v-model="filter.industry"
            placeholder="搜索行业名称"
            clearable
            @keyup.enter="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="行业代码">
          <el-input
            v-model="filter.ts_code"
            placeholder="搜索行业代码"
            clearable
            @keyup.enter="handleFilterChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计数据 -->
    <el-row :gutter="20" class="stats-row" v-if="!loading && tableData.length > 0">
      <el-col :xs="12" :sm="8" :md="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ pagination.total }}</div>
          <div class="stat-label">记录总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card class="stat-card up">
          <div class="stat-value">{{ formatAmount(totalNetBuy) }}</div>
          <div class="stat-label">总买入净额</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card class="stat-card down">
          <div class="stat-value">{{ formatAmount(totalNetSell) }}</div>
          <div class="stat-label">总卖出净额</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card :class="['stat-card', totalNetAmount >= 0 ? 'up' : 'down']">
          <div class="stat-value">{{ formatSignedAmount(totalNetAmount) }}</div>
          <div class="stat-label">净流入</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card v-loading="loading" class="data-card">
      <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
      <el-table
        v-if="tableData.length > 0"
        :data="tableData"
        style="width: 100%"
        :default-sort="{ prop: 'net_amount', order: 'descending' }"
        @sort-change="handleSortChange"
        highlight-current-row
        border
        stripe
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="trade_date" label="交易日期" width="120" sortable align="center" />
        <el-table-column prop="ts_code" label="行业代码" width="120" sortable />
        <el-table-column prop="industry" label="行业名称" min-width="140" sortable>
          <template #default="{ row }">
            <router-link :to="{ path: '/sector/detail', query: { code: row.ts_code, sectorType: 'industry', sectorName: row.industry } }" class="sector-link">
              {{ row.industry }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="lead_stock" label="领涨股" min-width="120" />
        <el-table-column prop="net_amount" label="净流入" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.net_amount)">{{ formatSignedAmount(row.net_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_buy_amount" label="买入净额" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span class="amount-up">{{ formatAmount(row.net_buy_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_sell_amount" label="卖出净额" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span class="amount-down">{{ formatAmount(row.net_sell_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="close" label="收盘价" width="100" sortable align="right">
          <template #default="{ row }">
            <span>{{ formatNumber(row.close) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pct_change" label="涨跌幅" width="100" sortable align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row.pct_change)">{{ formatChange(row.pct_change) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="company_num" label="公司数" width="90" sortable align="center" />
        <el-table-column prop="pct_change_stock" label="领涨股涨幅" width="120" sortable align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row.pct_change_stock)">{{ formatChange(row.pct_change_stock) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="close_price" label="领涨股价" width="110" sortable align="right">
          <template #default="{ row }">
            <span>{{ formatNumber(row.close_price) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="pagination.total > 0">
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { basicDataApi } from '@/api'

const loading = ref(false)
const tableData = ref([])

const getToday = () => {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const filter = reactive({
  industry: '',
  trade_date: '',
  ts_code: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

// 禁用未来日期
const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

// 统计数据
const totalNetBuy = computed(() => tableData.value.reduce((sum, item) => sum + (item.net_buy_amount || 0), 0))
const totalNetSell = computed(() => tableData.value.reduce((sum, item) => sum + (item.net_sell_amount || 0), 0))
const totalNetAmount = computed(() => tableData.value.reduce((sum, item) => sum + (item.net_amount || 0), 0))

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const res = await basicDataApi.getMoneyflowIndThs({
      page: pagination.page,
      page_size: pagination.page_size,
      industry: filter.industry || null,
      trade_date: filter.trade_date || null,
      ts_code: filter.ts_code || null,
      sort_field: sortState.sort_field,
      sort_order: sortState.sort_order
    })
    if (res.success) {
      tableData.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total
        pagination.total_pages = res.pagination.total_pages
      }
      if (tableData.value.length > 0) {
        ElMessage.success(`成功获取 ${tableData.value.length} 条数据`)
      } else {
        ElMessage.info('暂无数据')
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
      tableData.value = []
    }
  } catch (err) {
    console.error('Failed to fetch moneyflow ind ths:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    tableData.value = []
  } finally {
    loading.value = false
  }
}

// 筛选变化
const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

// 获取最后交易日期
const initLastTradeDate = async () => {
  try {
    const res = await basicDataApi.getLastTradeDate()
    if (res.success && res.data) {
      filter.trade_date = res.data
    } else {
      filter.trade_date = getToday()
    }
  } catch (err) {
    console.error('Failed to get last trade date:', err)
    filter.trade_date = getToday()
  }
}

// 重置筛选
const resetFilter = () => {
  filter.industry = ''
  filter.trade_date = ''
  filter.ts_code = ''
  pagination.page = 1
  initLastTradeDate().then(() => fetchData())
}

// 分页变化
const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

// 排序变化
const sortState = reactive({
  sort_field: null,
  sort_order: null
})

const handleSortChange = ({ prop, order }) => {
  sortState.sort_field = prop || null
  sortState.sort_order = order || null
  pagination.page = 1
  fetchData()
}

// 格式化涨跌幅
const formatChange = (value) => {
  if (value === null || value === undefined) return '-'
  const prefix = value > 0 ? '+' : ''
  return prefix + value.toFixed(2) + '%'
}

// 涨跌幅样式
const getChangeClass = (value) => {
  if (value > 0) return 'change-up'
  if (value < 0) return 'change-down'
  return 'change-flat'
}

// 格式化金额（单位：亿）
const formatAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  return amount.toFixed(2) + '亿'
}

// 格式化金额（带符号）
const formatSignedAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  const prefix = amount > 0 ? '+' : ''
  return prefix + formatAmount(amount)
}

// 金额样式
const getAmountClass = (amount) => {
  if (amount > 0) return 'amount-up'
  if (amount < 0) return 'amount-down'
  return 'amount-flat'
}

// 格式化数字
const formatNumber = (value) => {
  if (value === null || value === undefined) return '-'
  return value.toFixed(2)
}

onMounted(async () => {
  await initLastTradeDate()
  fetchData()
})
</script>

<style scoped>
.moneyflow-ind-ths-page {
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
  gap: 15px;
  align-items: center;
}

.filter-card {
  margin-bottom: 20px;
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
  font-size: 20px;
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

.stat-label {
  font-size: 12px;
  color: #909399;
}

.data-card {
  min-height: 200px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.change-up {
  color: #f56c6c;
  font-weight: 600;
}

.change-down {
  color: #67c23a;
  font-weight: 600;
}

.change-flat {
  color: #909399;
}

.amount-up {
  color: #f56c6c;
  font-weight: 600;
}

.amount-down {
  color: #67c23a;
  font-weight: 600;
}

.amount-flat {
  color: #909399;
}

.sector-link {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.sector-link:hover {
  text-decoration: underline;
  color: #66b1ff;
}

@media (max-width: 768px) {
  .moneyflow-ind-ths-page {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
