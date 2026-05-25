<template>
  <div class="daily-score-view">
    <div class="page-header">
      <h2>每日量化评分</h2>
      <div class="header-actions">
        <el-select
          v-model="selectedDate"
          placeholder="选择日期"
          style="width: 160px"
          @change="handleDateChange"
        >
          <el-option
            v-for="date in availableDates"
            :key="date"
            :label="date"
            :value="date"
          />
        </el-select>
        <el-radio-group v-model="directionFilter" @change="handleDirectionChange" size="small">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="bullish">看多</el-radio-button>
          <el-radio-button label="neutral">中性</el-radio-button>
          <el-radio-button label="bearish">看空</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
        <el-button type="success" @click="copyTsCodes">
          <el-icon><CopyDocument /></el-icon>复制代码
        </el-button>
      </div>
    </div>

    <div v-if="summary" class="stats-row">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value">{{ summary.total }}</div>
        <div class="stat-label">评分股票</div>
      </el-card>
      <el-card class="stat-card stat-bullish" shadow="hover">
        <div class="stat-value">{{ summary.bullish }}</div>
        <div class="stat-label">看多</div>
      </el-card>
      <el-card class="stat-card stat-neutral" shadow="hover">
        <div class="stat-value">{{ summary.neutral }}</div>
        <div class="stat-label">中性</div>
      </el-card>
      <el-card class="stat-card stat-bearish" shadow="hover">
        <div class="stat-value">{{ summary.bearish }}</div>
        <div class="stat-label">看空</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value" :style="{ color: scoreColor(summary.avg_score) }">
          {{ summary.avg_score }}
        </div>
        <div class="stat-label">平均评分</div>
      </el-card>
    </div>

    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="table-header">
          <span>综合排名</span>
          <span v-if="selectedDate" class="date-label">{{ selectedDate }}</span>
        </div>
      </template>
      <el-table
        :data="filteredScores"
        stripe
        border
        size="small"
        :max-height="600"
        v-loading="loading"
      >
        <el-table-column prop="rank_in_watchlist" label="排名" width="60" align="center" sortable />
        <el-table-column prop="ts_code" label="代码" width="110">
          <template #default="{ row }">
            <a href="#" @click.prevent="openStockDetail(row.ts_code)" class="stock-link">
              {{ row.ts_code }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="100" />
        <el-table-column prop="industry" label="行业" width="100" />
        <el-table-column prop="composite_5d" label="5日评分" width="90" align="right" sortable>
          <template #default="{ row }">
            <span :style="{ color: scoreColor(row.composite_5d), fontWeight: 'bold' }">
              {{ formatScore(row.composite_5d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="composite_1d" label="1日" width="70" align="right">
          <template #default="{ row }">
            <span :style="{ color: scoreColor(row.composite_1d) }">
              {{ formatScore(row.composite_1d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="composite_3d" label="3日" width="70" align="right">
          <template #default="{ row }">
            <span :style="{ color: scoreColor(row.composite_3d) }">
              {{ formatScore(row.composite_3d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="composite_10d" label="10日" width="70" align="right">
          <template #default="{ row }">
            <span :style="{ color: scoreColor(row.composite_10d) }">
              {{ formatScore(row.composite_10d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="direction_5d" label="方向" width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="directionTagType(row.direction_5d)"
              size="small"
            >
              {{ directionLabel(row.direction_5d) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trend_score" label="趋势" width="70" align="right" />
        <el-table-column prop="momentum_score" label="动量" width="70" align="right" />
        <el-table-column prop="volume_price_score" label="量价" width="70" align="right" />
        <el-table-column prop="score_change_5d" label="变化" width="80" align="right" sortable>
          <template #default="{ row }">
            <span
              v-if="row.score_change_5d"
              :class="row.score_change_5d > 0 ? 'change-up' : 'change-down'"
            >
              {{ row.score_change_5d > 0 ? '+' : '' }}{{ formatScore(row.score_change_5d) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh, CopyDocument } from '@element-plus/icons-vue'
import { dailyScoreApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const selectedDate = ref('')
const availableDates = ref([])
const directionFilter = ref('')
const summary = ref(null)
const scores = ref([])

const filteredScores = computed(() => {
  if (!directionFilter.value) return scores.value
  return scores.value.filter(s => s.direction_5d === directionFilter.value)
})

const scoreColor = (score) => {
  if (score == null) return '#718096'
  if (score >= 70) return '#e53e3e'
  if (score >= 50) return '#d69e2e'
  if (score >= 35) return '#718096'
  return '#38a169'
}

const directionTagType = (direction) => {
  if (direction === 'bullish') return 'danger'
  if (direction === 'bearish') return 'success'
  return 'warning'
}

const directionLabel = (direction) => {
  if (direction === 'bullish') return '看多'
  if (direction === 'bearish') return '看空'
  return '中性'
}

const formatScore = (val) => {
  if (val == null) return '-'
  return Number(val).toFixed(1)
}

const openStockDetail = (tsCode) => {
  window.open(`/stock/${tsCode}`, '_blank')
}

const copyTsCodes = async () => {
  if (!filteredScores.value.length) {
    ElMessage.warning('没有数据可复制')
    return
  }
  const text = filteredScores.value.map(s => s.ts_code).join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`已复制 ${filteredScores.value.length} 条代码`)
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

const loadDates = async () => {
  try {
    const res = await dailyScoreApi.getDates()
    if (res.success && res.data) {
      availableDates.value = res.data
      if (!selectedDate.value && res.data.length > 0) {
        selectedDate.value = res.data[0]
      }
    }
  } catch (e) {
    console.error('load dates failed', e)
  }
}

const loadSummary = async () => {
  if (!selectedDate.value) return
  try {
    const res = await dailyScoreApi.getSummary(selectedDate.value)
    if (res.success && res.data) {
      summary.value = res.data
    }
  } catch (e) {
    console.error('load summary failed', e)
  }
}

const loadScores = async () => {
  if (!selectedDate.value) return
  try {
    loading.value = true
    const res = await dailyScoreApi.getScores(selectedDate.value)
    if (res.success && res.data) {
      scores.value = res.data
    }
  } catch (e) {
    ElMessage.error('加载评分数据失败')
    console.error('load scores failed', e)
  } finally {
    loading.value = false
  }
}

const loadData = async () => {
  await loadSummary()
  await loadScores()
}

const handleDateChange = () => {
  loadData()
}

const handleDirectionChange = () => {
}

onMounted(async () => {
  await loadDates()
  if (selectedDate.value) {
    await loadData()
  }
})
</script>

<style scoped>
.daily-score-view {
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
  font-size: 1.5em;
  color: #2d3748;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-value {
  font-size: 2em;
  font-weight: bold;
  color: #2d3748;
  margin-bottom: 5px;
}

.stat-label {
  color: #718096;
  font-size: 0.9em;
}

.stat-bullish .stat-value {
  color: #e53e3e;
}

.stat-bearish .stat-value {
  color: #38a169;
}

.stat-neutral .stat-value {
  color: #d69e2e;
}

.table-card {
  margin-top: 10px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date-label {
  color: #718096;
  font-size: 0.9em;
}

.stock-link {
  color: #409eff;
  text-decoration: none;
}

.stock-link:hover {
  text-decoration: underline;
}

.change-up {
  color: #e53e3e;
  font-weight: bold;
}

.change-down {
  color: #38a169;
  font-weight: bold;
}
</style>
