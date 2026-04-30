<template>
  <div class="industry-daily-flow-page">
    <div class="page-header">
      <h2>行业每日净流入</h2>
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
            clearable
          />
        </el-form-item>
        <el-form-item label="查询天数">
          <el-select v-model="filter.days" placeholder="选择天数" style="width: 120px" @change="handleFilterChange">
            <el-option label="5天" :value="5" />
            <el-option label="10天" :value="10" />
            <el-option label="20天" :value="20" />
            <el-option label="30天" :value="30" />
            <el-option label="60天" :value="60" />
            <el-option label="90天" :value="90" />
          </el-select>
        </el-form-item>
        <el-form-item label="行业名称">
          <el-input
            v-model="filter.industry"
            placeholder="搜索行业名称"
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

    <!-- 数据表格 -->
    <el-card v-loading="loading" class="data-card">
      <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
      <el-table
        v-if="tableData.length > 0"
        :data="tableData"
        style="width: 100%"
        :default-sort="{ prop: 'total_net_inflow', order: 'descending' }"
        @sort-change="handleSortChange"
        highlight-current-row
        border
        stripe
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="trade_date" label="交易日期" width="120" sortable align="center" />
        <el-table-column prop="industry" label="行业名称" min-width="140" sortable>
          <template #default="{ row }">
            <router-link
              :to="{ path: '/sector/detail', query: { code: row.industry_code, sectorType: 'industry', sectorName: row.industry } }"
              class="sector-link"
            >
              {{ row.industry }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="stock_count" label="股票数" width="90" sortable align="center" />
        <el-table-column prop="total_net_inflow" label="净流入" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.total_net_inflow)">{{ formatSignedAmount(row.total_net_inflow) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_buy_amount" label="总买入" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span class="amount-up">{{ formatAmount(row.total_buy_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_sell_amount" label="总卖出" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span class="amount-down">{{ formatAmount(row.total_sell_amount) }}</span>
          </template>
        </el-table-column>
      </el-table>
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

const filter = reactive({
  trade_date: '',
  days: 5,
  industry: ''
})

const sortState = reactive({
  sort_field: null,
  sort_order: null
})

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const totalBuy = computed(() => tableData.value.reduce((sum, item) => sum + (item.total_buy_amount || 0), 0))
const totalSell = computed(() => tableData.value.reduce((sum, item) => sum + (item.total_sell_amount || 0), 0))
const totalNet = computed(() => tableData.value.reduce((sum, item) => sum + (item.total_net_inflow || 0), 0))

const fetchData = async () => {
  loading.value = true
  try {
    const res = await basicDataApi.getIndustryDailyFlow({
      trade_date: filter.trade_date || null,
      days: filter.days,
      industry: filter.industry || null,
      sort_field: sortState.sort_field,
      sort_order: sortState.sort_order
    })
    if (res.success) {
      tableData.value = res.data || []
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
    console.error('Failed to fetch industry daily flow:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  fetchData()
}

const resetFilter = () => {
  filter.trade_date = ''
  filter.days = 5
  filter.industry = ''
  sortState.sort_field = null
  sortState.sort_order = null
  fetchData()
}

const handleSortChange = ({ prop, order }) => {
  sortState.sort_field = prop || null
  sortState.sort_order = order || null
  fetchData()
}

const formatAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  // 数据库单位为万元，转换为亿展示
  const yi = amount / 10000
  return yi.toFixed(2) + '亿'
}

const formatSignedAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  const prefix = amount > 0 ? '+' : ''
  return prefix + formatAmount(amount)
}

const getAmountClass = (amount) => {
  if (amount > 0) return 'amount-up'
  if (amount < 0) return 'amount-down'
  return 'amount-flat'
}

const fetchLastTradeDate = async () => {
  try {
    const res = await basicDataApi.getLastTradeDate()
    if (res.success && res.data) {
      const dateStr = typeof res.data === 'string' ? res.data : res.data.cal_date
      if (dateStr) {
        filter.trade_date = dateStr
      }
    }
  } catch (err) {
    console.error('Failed to fetch last trade date:', err)
  }
}

onMounted(async () => {
  await fetchLastTradeDate()
  fetchData()
})
</script>

<style scoped>
.industry-daily-flow-page {
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
  .industry-daily-flow-page {
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
