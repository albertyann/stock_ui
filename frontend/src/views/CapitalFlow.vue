<template>
  <div class="capital-flow-page">

    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filter">
        <el-form-item label="统计天数">
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
        <el-table-column prop="ts_code" label="行业代码" width="120" sortable />
        <el-table-column prop="industry" label="行业名称" min-width="140" sortable>
          <template #default="{ row }">
            <router-link :to="{ path: '/sector/detail', query: { code: row.ts_code, sectorType: 'industry', sectorName: row.industry } }" class="sector-link">
              {{ row.industry }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="total_net_inflow" label="净流入" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.total_net_inflow)">{{ formatSignedAmount(row.total_net_inflow) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_inflow" label="总买入净额" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span class="amount-up">{{ formatAmount(row.total_inflow) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_outflow" label="总卖出净额" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span class="amount-down">{{ formatAmount(row.total_outflow) }}</span>
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
  industry: '',
  days: 5,
  ts_code: ''
})

// 统计数据
const totalInflow = computed(() => tableData.value.reduce((sum, item) => sum + (item.total_inflow || 0), 0))
const totalOutflow = computed(() => tableData.value.reduce((sum, item) => sum + (item.total_outflow || 0), 0))
const totalNetInflow = computed(() => tableData.value.reduce((sum, item) => sum + (item.total_net_inflow || 0), 0))

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const res = await basicDataApi.getCapitalFlow({
      days: filter.days,
      industry: filter.industry || null,
      ts_code: filter.ts_code || null,
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
    console.error('Failed to fetch capital flow:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    tableData.value = []
  } finally {
    loading.value = false
  }
}

// 筛选变化
const handleFilterChange = () => {
  fetchData()
}

// 重置筛选
const resetFilter = () => {
  filter.industry = ''
  filter.days = 20
  filter.ts_code = ''
  sortState.sort_field = null
  sortState.sort_order = null
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
  fetchData()
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

// 格式化占比
const formatRatio = (net, total) => {
  if (!total || total === 0) return '-'
  const ratio = (net / total) * 100
  const prefix = ratio > 0 ? '+' : ''
  return prefix + ratio.toFixed(2) + '%'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.capital-flow-page {
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
  .capital-flow-page {
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
