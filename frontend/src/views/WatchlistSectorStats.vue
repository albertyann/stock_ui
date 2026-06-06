<template>
  <div class="sector-stats-page">
    <div class="page-header">
      <h2>关注板块</h2>
      <el-button type="primary" @click="fetchData" :loading="loading">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <el-row :gutter="20" class="summary-row">
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-label">关注板块数</div>
          <div class="summary-value">{{ stats.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-label">上涨板块数</div>
          <div class="summary-value up">{{ upIndustriesCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-label">下跌板块数</div>
          <div class="summary-value down">{{ downIndustriesCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-label">总关注股票数</div>
          <div class="summary-value">{{ totalStocks }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="stats-table-card" v-loading="loading">
      <template #header>
        <div class="table-header">
          <span>板块统计详情</span>
          <el-radio-group v-model="sortBy" size="small">
            <el-radio-button label="stocks">按股票数</el-radio-button>
            <el-radio-button label="up">按上涨数</el-radio-button>
            <el-radio-button label="change">按平均涨幅</el-radio-button>
            <el-radio-button label="amount">按交易金额</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="sortedStats" stripe style="width: 100%">
        <el-table-column prop="industry" label="板块" min-width="120" sortable />
        <el-table-column prop="total_stocks" label="股票数" width="100" sortable />
        <el-table-column label="涨跌分布" width="200">
          <template #default="{ row }">
            <div class="up-down-bar">
              <div
                class="bar-segment bar-up"
                :style="{ width: getUpPct(row) + '%' }"
                :title="`上涨 ${row.up_count} 只`"
              >
                {{ row.up_count > 0 ? row.up_count : '' }}
              </div>
              <div
                class="bar-segment bar-flat"
                :style="{ width: getFlatPct(row) + '%' }"
                :title="`平盘 ${row.flat_count} 只`"
              >
                {{ row.flat_count > 0 ? row.flat_count : '' }}
              </div>
              <div
                class="bar-segment bar-down"
                :style="{ width: getDownPct(row) + '%' }"
                :title="`下跌 ${row.down_count} 只`"
              >
                {{ row.down_count > 0 ? row.down_count : '' }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="up_count" label="上涨" width="80" sortable>
          <template #default="{ row }">
            <span class="up-text">{{ row.up_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="down_count" label="下跌" width="80" sortable>
          <template #default="{ row }">
            <span class="down-text">{{ row.down_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="flat_count" label="平盘" width="80" sortable />
        <el-table-column label="平均涨幅" width="120" sortable :sort-method="sortByAvgChange">
          <template #default="{ row }">
            <span :class="getChangeClass(row.avg_change_pct)">
              {{ formatChange(row.avg_change_pct) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="当天交易额" width="150" sortable :sort-method="sortByTodayAmount">
          <template #default="{ row }">
            {{ formatAmount(row.today_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="前一天交易额" width="150" sortable :sort-method="sortByPrevAmount">
          <template #default="{ row }">
            {{ formatAmount(row.prev_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="交易额变化" width="130" sortable :sort-method="sortByAmountChange">
          <template #default="{ row }">
            <span :class="getAmountChangeClass(row)">
              {{ formatAmountChange(row.amount_change_pct) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { watchlistApi } from '@/api'
import { ElMessage } from 'element-plus'

const stats = ref([])
const loading = ref(false)
const sortBy = ref('stocks')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await watchlistApi.getSectorStats()
    if (res.success && res.data) {
      stats.value = res.data
    }
  } catch (e) {
    console.error('Failed to fetch sector stats:', e)
    ElMessage.error('加载板块统计数据失败')
  } finally {
    loading.value = false
  }
}

const totalStocks = computed(() => stats.value.reduce((sum, s) => sum + s.total_stocks, 0))

const upIndustriesCount = computed(() =>
  stats.value.filter(s => s.avg_change_pct > 0).length
)

const downIndustriesCount = computed(() =>
  stats.value.filter(s => s.avg_change_pct < 0).length
)

const sortedStats = computed(() => {
  const data = [...stats.value]
  switch (sortBy.value) {
    case 'up':
      return data.sort((a, b) => b.up_count - a.up_count)
    case 'change':
      return data.sort((a, b) => (b.avg_change_pct || 0) - (a.avg_change_pct || 0))
    case 'amount':
      return data.sort((a, b) => (b.today_amount || 0) - (a.today_amount || 0))
    case 'stocks':
    default:
      return data.sort((a, b) => b.total_stocks - a.total_stocks)
  }
})

const getUpPct = (row) => {
  if (!row.total_stocks) return 0
  return (row.up_count / row.total_stocks) * 100
}

const getDownPct = (row) => {
  if (!row.total_stocks) return 0
  return (row.down_count / row.total_stocks) * 100
}

const getFlatPct = (row) => {
  if (!row.total_stocks) return 0
  return (row.flat_count / row.total_stocks) * 100
}

const getChangeClass = (change) => {
  if (!change) return 'flat-text'
  return change > 0 ? 'up-text' : change < 0 ? 'down-text' : 'flat-text'
}

const formatChange = (change) => {
  if (change === null || change === undefined) return '-'
  const sign = change > 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}

const formatAmount = (amount) => {
  if (!amount) return '-'
  if (amount >= 100000000) {
    return (amount / 100000000).toFixed(2) + '亿'
  }
  if (amount >= 10000) {
    return (amount / 10000).toFixed(2) + '万'
  }
  return amount.toFixed(2)
}

const getAmountChangeClass = (row) => {
  if (!row.amount_change_pct) return 'flat-text'
  return row.amount_change_pct > 0 ? 'up-text' : 'down-text'
}

const formatAmountChange = (change) => {
  if (change === null || change === undefined) return '-'
  const sign = change > 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}

const sortByAvgChange = (a, b) => (a.avg_change_pct || 0) - (b.avg_change_pct || 0)
const sortByTodayAmount = (a, b) => (a.today_amount || 0) - (b.today_amount || 0)
const sortByPrevAmount = (a, b) => (a.prev_amount || 0) - (b.prev_amount || 0)
const sortByAmountChange = (a, b) => (a.amount_change_pct || 0) - (b.amount_change_pct || 0)

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.sector-stats-page {
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
  font-size: 20px;
  color: #303133;
}

.summary-row {
  margin-bottom: 20px;
}

.summary-card {
  text-align: center;
}

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.summary-value.up {
  color: #f56c6c;
}

.summary-value.down {
  color: #67c23a;
}

.stats-table-card {
  margin-top: 10px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.up-down-bar {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  font-size: 12px;
  color: white;
  line-height: 24px;
  text-align: center;
}

.bar-segment {
  min-width: 0;
  transition: width 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-up {
  background-color: #f56c6c;
}

.bar-flat {
  background-color: #909399;
}

.bar-down {
  background-color: #67c23a;
}

.up-text {
  color: #f56c6c;
  font-weight: 600;
}

.down-text {
  color: #67c23a;
  font-weight: 600;
}

.flat-text {
  color: #909399;
}
</style>
