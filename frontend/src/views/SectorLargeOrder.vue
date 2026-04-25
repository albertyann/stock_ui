<template>
  <div class="sector-large-order-page">
    <div class="page-header">
      <h2>板块大单</h2>
      <div class="header-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择交易日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledDate"
          @change="handleDateChange"
          style="width: 160px"
        />
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <el-row :gutter="20" class="stats-row" v-if="!loading && data.length > 0">
      <el-col :xs="12" :sm="8" :md="4" :lg="4">
        <el-card class="stat-card">
          <div class="stat-value">{{ data.length }}</div>
          <div class="stat-label">板块数量</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="5" :lg="5">
        <el-card class="stat-card up">
          <div class="stat-value">{{ formatAmount(totalBuyLg) }}</div>
          <div class="stat-label">大单买入</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="5" :lg="5">
        <el-card class="stat-card down">
          <div class="stat-value">{{ formatAmount(totalSellLg) }}</div>
          <div class="stat-label">大单卖出</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="5" :lg="5">
        <el-card class="stat-card up">
          <div class="stat-value">{{ formatAmount(totalBuyElg) }}</div>
          <div class="stat-label">特大单买入</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="5" :lg="5">
        <el-card class="stat-card down">
          <div class="stat-value">{{ formatAmount(totalSellElg) }}</div>
          <div class="stat-label">特大单卖出</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card v-loading="loading" class="data-card">
      <el-empty v-if="!loading && data.length === 0" description="暂无数据" />
      <el-table
        v-if="data.length > 0"
        :data="data"
        style="width: 100%"
        :default-sort="{ prop: 'net_total_amount', order: 'descending' }"
        highlight-current-row
        border
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="industry" label="行业" min-width="140" sortable />
        <el-table-column prop="buy_lg_amount" label="大单买入" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span class="amount-up">{{ formatAmount(row.buy_lg_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sell_lg_amount" label="大单卖出" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span class="amount-down">{{ formatAmount(row.sell_lg_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_lg_amount" label="大单净额" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.net_lg_amount)">{{ formatSignedAmount(row.net_lg_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="buy_elg_amount" label="特大单买入" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span class="amount-up">{{ formatAmount(row.buy_elg_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sell_elg_amount" label="特大单卖出" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span class="amount-down">{{ formatAmount(row.sell_elg_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_elg_amount" label="特大单净额" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.net_elg_amount)">{{ formatSignedAmount(row.net_elg_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_total_amount" label="合计净额" min-width="120" sortable align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.net_total_amount)">{{ formatSignedAmount(row.net_total_amount) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { sectorApi } from '@/api'

const loading = ref(false)
const data = ref([])
const selectedDate = ref('')

// 获取今天的日期字符串 YYYY-MM-DD
const getToday = () => {
  const d = new Date()
  return d.toISOString().split('T')[0]
}

// 禁用未来日期
const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

// 统计数据
const totalBuyLg = computed(() => data.value.reduce((sum, item) => sum + (item.buy_lg_amount || 0), 0))
const totalSellLg = computed(() => data.value.reduce((sum, item) => sum + (item.sell_lg_amount || 0), 0))
const totalBuyElg = computed(() => data.value.reduce((sum, item) => sum + (item.buy_elg_amount || 0), 0))
const totalSellElg = computed(() => data.value.reduce((sum, item) => sum + (item.sell_elg_amount || 0), 0))

// 获取数据
const fetchData = async () => {
  if (!selectedDate.value) {
    ElMessage.warning('请选择交易日期')
    return
  }

  loading.value = true
  try {
    const response = await sectorApi.getSectorLargeOrders(selectedDate.value)
    if (response.success) {
      data.value = response.data || []
      ElMessage.success(`成功获取 ${data.value.length} 个板块数据`)
    } else {
      ElMessage.error(response.error || '获取数据失败')
      data.value = []
    }
  } catch (error) {
    console.error('Failed to fetch sector large orders:', error)
    ElMessage.error('获取数据失败：' + (error.message || '网络错误'))
    data.value = []
  } finally {
    loading.value = false
  }
}

// 日期变化
const handleDateChange = () => {
  fetchData()
}

// 格式化金额（无符号）—— moneyflow 金额单位为万
const formatAmount = (amount) => {
  if (!amount && amount !== 0) return '-'
  const absVal = Math.abs(amount)
  if (absVal >= 10000) {
    return (amount / 10000).toFixed(2) + '亿'
  }
  return amount.toFixed(2) + '万'
}

// 格式化金额（带符号）
const formatSignedAmount = (amount) => {
  if (!amount && amount !== 0) return '-'
  const prefix = amount > 0 ? '+' : ''
  return prefix + formatAmount(amount)
}

// 金额样式
const getAmountClass = (amount) => {
  if (amount > 0) return 'amount-up'
  if (amount < 0) return 'amount-down'
  return 'amount-flat'
}

onMounted(() => {
  selectedDate.value = getToday()
  fetchData()
})
</script>

<style scoped>
.sector-large-order-page {
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

@media (max-width: 768px) {
  .sector-large-order-page {
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
