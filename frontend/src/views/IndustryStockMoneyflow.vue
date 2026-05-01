<template>
  <div class="industry-stock-moneyflow-page">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="$router.back()" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <h2>{{ industryName }} - 个股资金流向</h2>
      </div>
      <div class="header-actions">
        <el-tag v-if="tradeDate" type="info" size="large">交易日期: {{ tradeDate }}</el-tag>
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <el-row :gutter="20" class="stats-row" v-if="!loading && tableData.length > 0">
      <el-col :xs="12" :sm="8" :md="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ tableData.length }}</div>
          <div class="stat-label">股票数量</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card :class="['stat-card', totalNetMf >= 0 ? 'up' : 'down']">
          <div class="stat-value">{{ formatSignedAmount(totalNetMf) }}</div>
          <div class="stat-label">行业净流入</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card class="stat-card up">
          <div class="stat-value">{{ formatAmount(totalBuy) }}</div>
          <div class="stat-label">总买入金额</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card class="stat-card down">
          <div class="stat-value">{{ formatAmount(totalSell) }}</div>
          <div class="stat-label">总卖出金额</div>
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
        highlight-current-row
        border
        stripe
        :default-sort="{ prop: 'net_mf_amount', order: 'descending' }"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="股票名称" min-width="120" sortable>
          <template #default="{ row }">
            <router-link :to="{ path: '/stock/' + row.ts_code }" class="stock-link">
              {{ row.name }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="ts_code" label="股票代码" width="110" sortable />
        <el-table-column prop="trade_date" label="交易日期" width="120" sortable align="center" />
        <el-table-column prop="net_mf_amount" label="净流入额（亿元）" min-width="150" sortable align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.net_mf_amount)">{{ formatSignedAmount(row.net_mf_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="小单" align="right">
          <el-table-column prop="buy_sm_amount" label="买入" min-width="110" sortable align="right">
            <template #default="{ row }">
              <span class="amount-up">{{ formatAmount(row.buy_sm_amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="sell_sm_amount" label="卖出" min-width="110" sortable align="right">
            <template #default="{ row }">
              <span class="amount-down">{{ formatAmount(row.sell_sm_amount) }}</span>
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="中单" align="right">
          <el-table-column prop="buy_md_amount" label="买入" min-width="110" sortable align="right">
            <template #default="{ row }">
              <span class="amount-up">{{ formatAmount(row.buy_md_amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="sell_md_amount" label="卖出" min-width="110" sortable align="right">
            <template #default="{ row }">
              <span class="amount-down">{{ formatAmount(row.sell_md_amount) }}</span>
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="大单" align="right">
          <el-table-column prop="buy_lg_amount" label="买入" min-width="110" sortable align="right">
            <template #default="{ row }">
              <span class="amount-up">{{ formatAmount(row.buy_lg_amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="sell_lg_amount" label="卖出" min-width="110" sortable align="right">
            <template #default="{ row }">
              <span class="amount-down">{{ formatAmount(row.sell_lg_amount) }}</span>
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="特大单" align="right">
          <el-table-column prop="buy_elg_amount" label="买入" min-width="110" sortable align="right">
            <template #default="{ row }">
              <span class="amount-up">{{ formatAmount(row.buy_elg_amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="sell_elg_amount" label="卖出" min-width="110" sortable align="right">
            <template #default="{ row }">
              <span class="amount-down">{{ formatAmount(row.sell_elg_amount) }}</span>
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, ArrowLeft } from '@element-plus/icons-vue'
import { basicDataApi } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const tradeDate = ref('')
const industryName = ref('')

const fetchData = async () => {
  const industry = route.query.industry
  if (!industry) {
    ElMessage.warning('缺少行业参数')
    router.push('/hot-industries')
    return
  }

  industryName.value = industry
  loading.value = true

  try {
    const res = await basicDataApi.getIndustryStockMoneyflow({
      industry: industry,
      trade_date: route.query.trade_date || null,
      limit: 100
    })

    if (res.success) {
      tableData.value = res.data || []
      if (res.meta) {
        tradeDate.value = res.meta.trade_date || ''
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
    console.error('Failed to fetch industry stock moneyflow:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    tableData.value = []
  } finally {
    loading.value = false
  }
}

// 统计数据
const totalNetMf = computed(() => tableData.value.reduce((sum, item) => sum + (item.net_mf_amount || 0), 0))
const totalBuy = computed(() => tableData.value.reduce((sum, item) =>
  sum + (item.buy_sm_amount || 0) + (item.buy_md_amount || 0) + (item.buy_lg_amount || 0) + (item.buy_elg_amount || 0), 0))
const totalSell = computed(() => tableData.value.reduce((sum, item) =>
  sum + (item.sell_sm_amount || 0) + (item.sell_md_amount || 0) + (item.sell_lg_amount || 0) + (item.sell_elg_amount || 0), 0))

// 格式化金额（单位：亿元，数据库值为万元）
const formatAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  return (amount / 1e4).toFixed(2) + '亿'
}

// 格式化金额（带符号）
const formatSignedAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  const prefix = amount > 0 ? '+' : ''
  return prefix + (amount / 1e4).toFixed(2) + '亿'
}

// 金额样式
const getAmountClass = (amount) => {
  if (amount > 0) return 'amount-up'
  if (amount < 0) return 'amount-down'
  return 'amount-flat'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.industry-stock-moneyflow-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.back-btn {
  padding: 8px 15px;
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

.stock-link {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.stock-link:hover {
  text-decoration: underline;
  color: #66b1ff;
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
  .industry-stock-moneyflow-page {
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
