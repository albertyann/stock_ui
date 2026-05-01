<template>
  <div class="hot-industries-page">
    <div class="page-header">
      <h2>火热行业</h2>
      <div class="header-actions">
        <el-button type="success" @click="copyIndustries">
          <el-icon><CopyDocument /></el-icon>拷贝
        </el-button>
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
          />
        </el-form-item>
        <el-form-item label="最小成交额(亿)">
          <el-input-number
            v-model="filter.min_amount_yi"
            :min="0"
            :step="1"
            :precision="0"
            style="width: 140px"
            @change="handleFilterChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 统计信息 -->
      <div class="stats-row" v-if="meta.trade_date">
        <el-row :gutter="20">
          <el-col :xs="12" :sm="8" :md="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ meta.total_industries || 0 }}</div>
              <div class="stat-label">火热行业数</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="8" :md="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ meta.trade_date || '-' }}</div>
              <div class="stat-label">统计日期</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="8" :md="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ formatAmount(totalAmount) }}</div>
              <div class="stat-label">总成交额</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="8" :md="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ totalStockCount }}</div>
              <div class="stat-label">涉及股票数</div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card v-loading="loading" class="data-card">
      <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
      <el-table
        v-if="tableData.length > 0"
        :data="tableData"
        style="width: 100%"
        :default-sort="{ prop: 'total_amount', order: 'descending' }"
        @sort-change="handleSortChange"
        highlight-current-row
        border
        stripe
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="amount_rank" label="成交额排名" width="110" sortable align="center">
          <template #default="{ row }">
            <el-tag :type="row.amount_rank <= 3 ? 'danger' : row.amount_rank <= 10 ? 'warning' : 'info'" effect="dark">
              {{ row.amount_rank }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业名称" min-width="160" sortable>
          <template #default="{ row }">
            <router-link
              :to="{ path: '/industry-stock-moneyflow', query: { industry: row.industry, trade_date: meta.trade_date } }"
              class="sector-link"
            >
              {{ row.industry }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="stock_count" label="股票数" width="100" sortable align="center" />
        <el-table-column prop="total_amount" label="成交额(亿)" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span class="amount-value">{{ formatAmount(row.total_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_amount" label="平均成交额(亿)" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span>{{ formatAmount(row.avg_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_pct_chg" label="平均涨跌幅" min-width="130" sortable align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row.avg_pct_chg)">{{ formatChange(row.avg_pct_chg) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, CopyDocument, Document } from '@element-plus/icons-vue'
import { basicDataApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const meta = reactive({
  trade_date: null,
  min_amount: 1e8,
  total_industries: 0
})

const filter = reactive({
  trade_date: '',
  min_amount_yi: 1
})

const sortState = reactive({
  sort_field: null,
  sort_order: null
})

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const totalAmount = computed(() => tableData.value.reduce((sum, item) => sum + (item.total_amount || 0), 0))
const totalStockCount = computed(() => tableData.value.reduce((sum, item) => sum + (item.stock_count || 0), 0))

const fetchData = async () => {
  loading.value = true
  try {
    const res = await basicDataApi.getHotIndustries({
      trade_date: filter.trade_date || null,
      min_amount: filter.min_amount_yi * 1e8,
      sort_field: sortState.sort_field,
      sort_order: sortState.sort_order
    })
    if (res.success) {
      tableData.value = res.data || []
      if (res.meta) {
        meta.trade_date = res.meta.trade_date
        meta.min_amount = res.meta.min_amount
        meta.total_industries = res.meta.total_industries
      }
      if (tableData.value.length > 0) {
        ElMessage.success(`成功获取 ${tableData.value.length} 个火热行业`)
      } else {
        ElMessage.info('暂无符合条件的行业')
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
      tableData.value = []
    }
  } catch (err) {
    console.error('Failed to fetch hot industries:', err)
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
  filter.min_amount_yi = 1
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
  return (amount / 1e8).toFixed(2)
}

const formatChange = (value) => {
  if (value === null || value === undefined) return '-'
  const prefix = value > 0 ? '+' : ''
  return prefix + value.toFixed(2) + '%'
}

const getChangeClass = (value) => {
  if (value > 0) return 'change-up'
  if (value < 0) return 'change-down'
  return 'change-flat'
}

const industryCodeMap = ref(new Map())

const getIndustryCode = (industry) => {
  if (industryCodeMap.value.has(industry)) {
    return industryCodeMap.value.get(industry)
  }
  return industry
}

const copyIndustries = async () => {
  if (tableData.value.length === 0) {
    ElMessage.warning('暂无数据可拷贝')
    return
  }
  const text = tableData.value.map(row => row.industry).join(',')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('行业名称已拷贝到剪贴板')
  } catch (err) {
    console.error('Failed to copy:', err)
    ElMessage.error('拷贝失败')
  }
}

const generateCommand = async () => {
  const industries = '元器件,电气设备,半导体,通信设备,专用机械,软件服务'
  const date = filter.trade_date || '2026-04-14'
  const command = `python screener_cli.py ma20-proximity --industry ${industries} --date ${date}`
  try {
    await navigator.clipboard.writeText(command)
    ElMessage.success('命令已拷贝到剪贴板')
  } catch (err) {
    console.error('Failed to copy command:', err)
    ElMessage.error('命令拷贝失败')
  }
}

const fetchIndustryCodes = async () => {
  try {
    const res = await basicDataApi.getMoneyflowIndThsIndustries()
    if (res.success && res.data) {
      const map = new Map()
      res.data.forEach(item => {
        if (item.name && item.ts_code) {
          map.set(item.name, item.ts_code)
        }
      })
      industryCodeMap.value = map
    }
  } catch (err) {
    console.error('Failed to fetch industry codes:', err)
  }
}

onMounted(async () => {
  await fetchIndustryCodes()
  fetchData()
})
</script>

<style scoped>
.hot-industries-page {
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
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
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

.stat-label {
  font-size: 12px;
  color: #909399;
}

.data-card {
  min-height: 200px;
}

.amount-value {
  color: #409eff;
  font-weight: 600;
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
  .hot-industries-page {
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
