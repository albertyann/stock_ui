<template>
  <div class="industry-daily-flow-page">
    <div class="page-header">
      <h2>行业每日净流入</h2>
      <div class="header-actions">
        <el-button type="warning" @click="generateCommand">
          <el-icon><Document /></el-icon>命令
        </el-button>
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
            clearable
            @change="handleFilterChange"
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

    <!-- 命令弹窗 -->
    <el-dialog
      v-model="commandDialogVisible"
      title="可用命令"
      width="900px"
      destroy-on-close
    >
      <el-table :data="commandList" style="width: 100%" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="command" label="命令名称" min-width="180" />
        <el-table-column prop="description" label="描述" min-width="250" />
        <el-table-column label="行业参数" width="90" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.useIndustry" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="copySingleCommand(row)"
            >
              <el-icon><CopyDocument /></el-icon>
              拷贝
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Document, CopyDocument } from '@element-plus/icons-vue'
import { basicDataApi } from '@/api'

const loading = ref(false)
const tableData = ref([])

const filter = reactive({
  trade_date: '',
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

// 命令弹窗相关
const commandDialogVisible = ref(false)

const commandList = ref([
  {
    command: 'ma-dual-crossover',
    description: 'MA5双均线金叉策略选股器（MA5上穿MA20且MA5上穿MA30）',
    type: 'screener',
    needsParams: true,
    useIndustry: true
  },
  {
    command: 'ma10-proximity',
    description: 'MA10回踩策略选股器（股价回落MA10附近+之前股价在MA10上方+MA60趋势向上）',
    type: 'screener',
    needsParams: true,
    useIndustry: true
  },
  {
    command: 'ma2560-proximity',
    description: 'MA25回踩策略选股器（股价回落MA25附近+之前股价在MA25上方+MA60趋势向上）',
    type: 'screener',
    needsParams: true,
    useIndustry: true
  },
  {
    command: 'rsi12-continuous',
    description: 'RSI12连续强势策略选股器（RSI12连续5天大于65）',
    type: 'screener',
    needsParams: true,
    useIndustry: true
  },
  {
    command: 'rsi12-continuous-20d',
    description: 'RSI12连续20个交易日大于50策略选股器',
    type: 'screener',
    needsParams: true,
    useIndustry: true
  },
  {
    command: 'rsi-strong',
    description: 'RSI强势策略选股器',
    type: 'screener',
    needsParams: true,
    useIndustry: true
  },
  {
    command: 'ema-cross',
    description: 'EMA9上穿EMA21策略选股器（近5日EMA9上穿EMA21金叉）',
    type: 'screener',
    needsParams: true,
    useIndustry: true
  }
])

const generateCommand = () => {
  commandDialogVisible.value = true
}

const copySingleCommand = async (item) => {
  let command = ''
  // 从页面表格中获取净流入大于 1 亿的行业列表（数据库单位为万元，1 亿 = 10000 万元）
  const industries = tableData.value
    .filter(row => row.total_net_inflow > 10000)
    .map(row => row.industry)
    .join(',')
  // 使用筛选日期
  const date = filter.trade_date || ''
  if (item.type === 'screener' && item.needsParams) {
    const industryParam = item.useIndustry && industries ? ` --industry ${industries}` : ''
    command = `python stock_cli.py ${item.command}${industryParam} --date ${date} --all`
  } else {
    command = `${item.command} --all`
  }

  try {
    await navigator.clipboard.writeText(command)
    ElMessage.success(`命令已拷贝: ${item.command}`)
  } catch (err) {
    console.error('Failed to copy command:', err)
    ElMessage.error('命令拷贝失败')
  }
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
  color: var(--text-primary);
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
  color: var(--accent);
  margin-bottom: 5px;
}

.stat-card.up .stat-value {
  color: var(--stock-up);
}

.stat-card.down .stat-value {
  color: var(--stock-down);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.data-card {
  min-height: 200px;
}

.amount-up {
  color: var(--stock-up);
  font-weight: 600;
}

.amount-down {
  color: var(--stock-down);
  font-weight: 600;
}

.amount-flat {
  color: var(--stock-flat);
}

.sector-link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.sector-link:hover {
  text-decoration: underline;
  color: var(--accent-hover);
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
