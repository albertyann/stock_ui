<template>
  <div class="page-container">
    <div class="page-header">
      <h2>股票评估</h2>
      <el-button type="primary" @click="fetchData" :loading="loading">刷新</el-button>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="策略">
          <el-select
            v-model="filter.strategy_name"
            placeholder="全部"
            clearable
            style="width: 200px"
            @change="handleFilterChange"
          >
            <el-option
              v-for="s in meta.strategies"
              :key="s"
              :label="s"
              :value="s"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="行业">
          <el-select
            v-model="filter.industry"
            placeholder="全部"
            clearable
            filterable
            style="width: 200px"
            @change="handleFilterChange"
          >
            <el-option
              v-for="ind in meta.industries"
              :key="ind"
              :label="ind"
              :value="ind"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="交易日期">
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
        <el-form-item label="股票代码">
          <el-input
            v-model="filter.ts_code"
            placeholder="如 600000 或 600000.SH"
            clearable
            style="width: 180px"
            @keyup.enter="handleFilterChange"
            @clear="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="最低分数">
          <el-select
            v-model="filter.min_score"
            placeholder="全部"
            clearable
            style="width: 110px"
            @change="handleFilterChange"
          >
            <el-option label="≥ 90" :value="90" />
            <el-option label="≥ 95" :value="95" />
            <el-option label="≥ 100" :value="100" />
            <el-option label="≥ 105" :value="105" />
            <el-option label="≥ 110" :value="110" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
        <el-form-item v-if="meta.latest_date">
          <span class="latest-date-hint">最新数据日期：{{ meta.latest_date }}</span>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="tableData" stripe border>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="detail-container">
              <pre class="detail-pre">{{ formatDetails(row.details) }}</pre>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="trade_date" label="日期" width="110" />
        <el-table-column prop="strategy_name" label="策略" min-width="140" show-overflow-tooltip />
        <el-table-column label="代码" width="110">
          <template #default="{ row }">
            <a
              :href="`/stock/${row.ts_code}`"
              target="_blank"
              rel="noopener"
              class="stock-link"
            >
              {{ row.ts_code }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="110" show-overflow-tooltip />
        <el-table-column prop="industry" label="行业" width="120" show-overflow-tooltip />
        <el-table-column label="雪球" width="70" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="openXueqiu(row)">雪球</el-button>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getScoreTagType(row.score)">
              {{ formatScore(row.score) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最新价" width="100" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.details?.latest_price) }}
          </template>
        </el-table-column>
        <el-table-column label="涨跌幅" width="100" align="right">
          <template #default="{ row }">
            <span :style="{ color: getChangeColor(row.details?.latest_change_pct) }">
              {{ formatChangePct(row.details?.latest_change_pct) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="RSI6" width="80" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.details?.rsi6, 1) }}
          </template>
        </el-table-column>
        <el-table-column label="量比" width="80" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.details?.volume_ratio, 2) }}
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !tableData.length" description="暂无评估数据" />

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
import { screeningApi } from '@/api'
import { openXueqiu } from '@/utils/stock'

const loading = ref(false)
const tableData = ref([])

const meta = reactive({
  strategies: [],
  industries: [],
  latest_date: null
})

const filter = reactive({
  strategy_name: null,
  industry: null,
  ts_code: '',
  min_score: null,
  dateRange: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

const fetchMeta = async () => {
  try {
    const res = await screeningApi.getResultsMeta()
    if (res.success && res.data) {
      meta.strategies = res.data.strategies || []
      meta.industries = res.data.industries || []
      meta.latest_date = res.data.latest_date || null
    }
  } catch (err) {
    // 元数据加载失败不阻塞主流程
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      strategy_name: filter.strategy_name || null,
      industry: filter.industry || null,
      ts_code: filter.ts_code || null,
      min_score: filter.min_score ?? null,
      date_start: filter.dateRange ? filter.dateRange[0] : null,
      date_end: filter.dateRange ? filter.dateRange[1] : null
    }
    const res = await screeningApi.getResults(params)
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
  filter.strategy_name = null
  filter.industry = null
  filter.ts_code = ''
  filter.min_score = null
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

const getScoreTagType = (score) => {
  if (score === null || score === undefined) return 'info'
  if (score >= 95) return 'danger'
  if (score >= 90) return 'warning'
  return 'info'
}

const formatScore = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(1)
}

const formatPrice = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(2)
}

const formatNumber = (val, digits = 2) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(digits)
}

const formatChangePct = (val) => {
  if (val === null || val === undefined) return '-'
  const num = Number(val)
  return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`
}

const getChangeColor = (val) => {
  if (val === null || val === undefined) return 'inherit'
  const num = Number(val)
  if (num > 0) return '#f56c6c'
  if (num < 0) return '#67c23a'
  return 'inherit'
}

const formatDetails = (details) => {
  if (!details) return '无明细数据'
  return JSON.stringify(details, null, 2)
}

onMounted(() => {
  fetchMeta()
  fetchData()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
}
.filter-card {
  margin-bottom: 20px;
}
.latest-date-hint {
  color: var(--text-secondary, #909399);
  font-size: 13px;
}
.stock-link {
  color: var(--accent);
  text-decoration: none;
  cursor: pointer;
}
.stock-link:hover {
  text-decoration: underline;
}
.detail-container {
  max-height: 300px;
  overflow: auto;
  margin: 10px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}
.detail-pre {
  margin: 0;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-primary);
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
