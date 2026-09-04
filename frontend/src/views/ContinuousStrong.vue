<template>
  <div class="page-container">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="策略">
          <el-select v-model="filter.strategy_name" style="width: 220px" disabled>
            <el-option label="RsiStrong" value="RsiStrong" />
          </el-select>
        </el-form-item>
        <el-form-item label="5天内达标天数">
          <el-select v-model="filter.days" style="width: 120px" @change="handleFilterChange">
            <el-option v-for="n in [2, 3, 4, 5]" :key="n" :label="`${n} 天`" :value="n" />
          </el-select>
        </el-form-item>
        <el-form-item label="最低评分">
          <el-input-number
            v-model="filter.min_score"
            :min="1"
            :max="100"
            :step="1"
            @change="handleFilterChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">查询</el-button>
        </el-form-item>
      </el-form>
      <div v-if="dates.length > 0" class="date-range-info">
        <span>统计区间：</span>
        <el-tag v-for="d in dates" :key="d" size="small" class="date-tag">{{ d }}</el-tag>
      </div>
    </el-card>

    <el-card class="summary-card">
      <div v-if="hasSummary" class="summary-bar">
        <div class="summary-item">
          <span class="summary-label">次日上涨概率</span>
          <span class="summary-value" :class="summary.up_rate >= 0.5 ? 'up' : 'down'">
            {{ formatRate(summary.up_rate) }}
          </span>
          <span v-if="summary.ci95" class="summary-sub">
            95% CI [{{ formatRate(summary.ci95.lo) }}, {{ formatRate(summary.ci95.hi) }}]
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">全市场基准</span>
          <span class="summary-value">{{ formatRate(summary.market_baseline_up_rate) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">超额 (信号 − 基准)</span>
          <span class="summary-value" :class="excessClass">
            {{ formatSignedRate(summary.excess) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">次日平均涨跌幅</span>
          <span class="summary-value" :class="avgPctClass">
            {{ formatSignedPct(summary.avg_pct_chg) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">样本</span>
          <span class="summary-value">{{ summary.valid_events }}</span>
          <span class="summary-sub">/ {{ summary.total_events }} 事件</span>
        </div>
      </div>
      <div v-else class="summary-empty">暂无评估数据</div>
    </el-card>

    <el-card v-loading="loading">
      <el-empty v-if="!loading && stocks.length === 0" description="暂无强势信号" />

      <el-table
        v-if="stocks.length > 0"
        :data="pagedStocks"
        stripe
        :default-sort="{ prop: 'avg_score', order: 'descending' }"
      >
        <el-table-column label="代码" width="130">
          <template #default="{ row }">
            <span class="stock-code">{{ row.ts_code }}</span>
          </template>
        </el-table-column>
        <el-table-column label="名称" min-width="130">
          <template #default="{ row }">
            <span class="stock-name">{{ row.name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="市场" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="getMarketTypeTag(row.ts_code)">
              {{ getMarketType(row.ts_code) || '-' }}
            </el-tag>
            <el-tag>
              {{ row.industry || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="过去5天达标" prop="days_continuous" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="success">{{ row.days_continuous }} / 5 天</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="历史次日胜率" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.hist && row.hist.up_rate !== null" :class="histClass(row.hist)">
              {{ formatRate(row.hist.up_rate) }} <span class="hist-n">(n={{ row.hist.n }})</span>
            </span>
            <span v-else class="cell-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="最近信号次日" width="130" align="center">
          <template #default="{ row }">
            <template v-if="row.next_day && row.next_day.next_pct_chg !== null">
              <div :class="row.next_day.is_up ? 'pct-up' : 'pct-down'">
                {{ formatSignedPct(row.next_day.next_pct_chg) }}
              </div>
              <div v-if="row.next_day.next_date" class="next-date">{{ row.next_day.next_date }}</div>
            </template>
            <span v-else class="cell-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-for="d in dates"
          :key="d"
          :label="`${d} 评分`"
          min-width="130"
          align="center"
        >
          <template #default="{ row }">
            <span :class="getScoreClass(row.scores?.[d])">{{ formatScore(row.scores?.[d]) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="平均分" prop="avg_score" width="100" sortable align="center">
          <template #default="{ row }">
            <span class="avg-score">{{ formatScore(row.avg_score) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="viewDetail(row)">详情</el-button>
            <el-button type="primary" size="small" link @click="openXueqiu(row)">雪球</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[20, 50, 100]"
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
import { screeningApi } from '@/api'
import { getMarketType, getMarketTypeTag, openXueqiu } from '@/utils/stock'

const loading = ref(false)
const stocks = ref([])
const dates = ref([])
const summary = ref({})

const filter = reactive({
  strategy_name: 'RsiStrong',
  days: 2,
  min_score: 95
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const pagedStocks = computed(() => {
  const start = (pagination.page - 1) * pagination.page_size
  return stocks.value.slice(start, start + pagination.page_size)
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await screeningApi.getStrongContinuousEval({
      strategy_name: filter.strategy_name,
      days: filter.days,
      min_score: filter.min_score
    })
    if (res.success) {
      stocks.value = res.data || []
      dates.value = res.dates || []
      summary.value = res.summary || {}
      pagination.total = stocks.value.length
    } else {
      ElMessage.error(res.error || '获取数据失败')
    }
  } catch (err) {
    console.error('Failed to fetch strong continuous signals:', err)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page) => {
  pagination.page = page
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
}

const viewDetail = (stock) => {
  if (!stock.ts_code) return
  window.open(`/stock/${stock.ts_code}`, '_blank')
}

const formatScore = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(2)
}

const getScoreClass = (val) => {
  if (val === null || val === undefined) return ''
  return Number(val) >= filter.min_score ? 'score-high' : 'score-mid'
}

const hasSummary = computed(
  () => summary.value && summary.value.up_rate !== null && summary.value.up_rate !== undefined
)

const excessClass = computed(() => {
  const v = summary.value?.excess
  if (v === null || v === undefined) return 'neutral'
  return v >= 0 ? 'up' : 'down'
})

const avgPctClass = computed(() => {
  const v = summary.value?.avg_pct_chg
  if (v === null || v === undefined) return 'neutral'
  return v >= 0 ? 'up' : 'down'
})

const formatRate = (val) => {
  if (val === null || val === undefined) return '-'
  return `${(Number(val) * 100).toFixed(1)}%`
}

const formatSignedRate = (val) => {
  if (val === null || val === undefined) return '-'
  const pct = Number(val) * 100
  return `${pct > 0 ? '+' : ''}${pct.toFixed(2)}%`
}

const formatSignedPct = (val) => {
  if (val === null || val === undefined) return '-'
  const n = Number(val)
  return `${n > 0 ? '+' : ''}${n.toFixed(2)}%`
}

const histClass = (hist) => {
  if (!hist || hist.up_rate === null || hist.up_rate === undefined) return 'cell-muted'
  return Number(hist.up_rate) >= 0.5 ? 'pct-up' : 'pct-down'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.summary-card {
  margin-bottom: 20px;
}

.summary-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 12px;
  color: var(--text-muted);
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.summary-value.up {
  color: var(--stock-up);
}

.summary-value.down {
  color: var(--stock-down);
}

.summary-value.neutral {
  color: var(--text-muted);
}

.summary-sub {
  font-size: 12px;
  color: var(--text-muted);
}

.summary-empty {
  font-size: 13px;
  color: var(--text-muted);
}

.pct-up {
  color: var(--stock-up);
  font-weight: 600;
}

.pct-down {
  color: var(--stock-down);
  font-weight: 600;
}

.cell-muted {
  color: var(--text-muted);
}

.hist-n {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-muted);
}

.next-date {
  font-size: 12px;
  color: var(--text-muted);
}

.date-range-info {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-muted);
}

.date-tag {
  margin-left: 6px;
}

.stock-code {
  font-size: 13px;
  color: var(--text-muted);
}

.stock-name {
  font-weight: 600;
  color: var(--text-primary);
}

.avg-score {
  font-weight: 600;
  color: var(--accent);
}

.score-high {
  color: var(--stock-up);
  font-weight: 600;
}

.score-mid {
  color: var(--text-primary);
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 修复 fixed(sticky) 列背景透明：横向滚动时下层内容会透出。
   正常行用不透明卡片背景覆盖。不加 !important，
   让全局斑马纹/悬停的 !important 规则继续作用于 fixed 单元格 */
:deep(.el-table .el-table__body td.el-table-fixed-column--left),
:deep(.el-table .el-table__body td.el-table-fixed-column--right) {
  background-color: var(--bg-card-solid);
}
</style>
