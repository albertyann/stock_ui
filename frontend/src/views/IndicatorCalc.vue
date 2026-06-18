<template>
  <div class="page-container">
    <div class="page-header">
      <h2>指标计算</h2>
      <el-button
        type="primary"
        :loading="computing"
        :disabled="computing"
        @click="handleCompute"
      >
        <el-icon v-if="!computing"><Refresh /></el-icon>
        {{ computing ? '计算中...' : '刷新计算' }}
      </el-button>
    </div>

    <el-alert
      v-if="computing"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      正在批量计算 watchlist 全部股票的 RSI12 / MA10 / MA25 三项指标，预计 1-3 分钟，请勿关闭页面...
    </el-alert>

    <el-alert
      v-if="summary && summary.errors && summary.errors.length > 0"
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
    >
      <template #title>
        部分指标计算失败 ({{ summary.errors.length }} 项)
      </template>
      <div v-for="(err, idx) in summary.errors" :key="idx" style="font-size: 12px; line-height: 1.6">
        {{ err }}
      </div>
    </el-alert>

    <el-card v-if="summary" class="summary-card" shadow="never">
      <div class="summary-grid">
        <div class="summary-item">
          <div class="summary-label">上次计算日期</div>
          <div class="summary-value">{{ summary.end_date || '—' }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">计算耗时</div>
          <div class="summary-value">{{ formatDuration(summary.duration_sec) }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">股票总数</div>
          <div class="summary-value">{{ summary.watchlist_total ?? 0 }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">RSI12 命中</div>
          <div class="summary-value hit">{{ summary.passed_counts?.rsi12 ?? 0 }} 只</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">MA10 命中</div>
          <div class="summary-value hit">{{ summary.passed_counts?.ma10 ?? 0 }} 只</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">MA25 命中</div>
          <div class="summary-value hit">{{ summary.passed_counts?.ma2560 ?? 0 }} 只</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">计算时间</div>
          <div class="summary-value small">{{ formatTime(summary.computed_at) }}</div>
        </div>
      </div>
    </el-card>

    <el-card v-loading="loading" style="margin-top: 16px">
      <el-table
        v-if="tableRows.length > 0"
        :data="tableRows"
        stripe
        border
        :default-sort="{ prop: 'hitCount', order: 'descending' }"
        :row-class-name="rowClassName"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="ts_code" label="代码" width="120" sortable />
        <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.name || row.ts_code }}
          </template>
        </el-table-column>
        <el-table-column
          label="板块"
          width="100"
          align="center"
          column-key="board"
          :filters="boardFilters"
          :filter-method="filterBoard"
        >
          <template #default="{ row }">
            <el-tag size="small" :type="row.boardType.type">
              {{ row.boardType.emoji }} {{ row.boardType.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="涨幅" width="100" align="center" sortable :sort-method="sortByChangePct">
          <template #default="{ row }">
            <span v-if="row.change_pct !== null" :class="getChangeClass(row.change_pct)">
              {{ row.change_pct >= 0 ? '+' : '' }}{{ row.change_pct.toFixed(2) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="RSI12强势" width="130" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.rsi12" type="success" size="small">
              {{ row.rsi12.score.toFixed(0) }} 分
            </el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="MA10回踩" width="130" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.ma10" type="warning" size="small">
              {{ row.ma10.score.toFixed(0) }} 分
            </el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="MA25回踩" width="130" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.ma2560" type="primary" size="small">
              {{ row.ma2560.score.toFixed(0) }} 分
            </el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="hitCount"
          label="综合命中"
          width="110"
          align="center"
          sortable
        >
          <template #default="{ row }">
            <span :class="['hit-badge', `hit-${row.hitCount}`]">{{ row.hitCount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="goDetail(row.ts_code)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="暂无缓存数据，请点击「刷新计算」按钮生成" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, defineCustomElement, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { indicatorCalcApi, watchlistApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const computing = ref(false)
const summary = ref(null)
const stocksMap = ref({})
const nameMap = ref({})
const priceMap = ref({})

const getBoardType = (tsCode) => {
  if (!tsCode) return { emoji: '', label: '', type: 'info' }

  const code = tsCode.split('.')[0]
  const prefix = code.substring(0, 3)

  // 科创板
  if (['688', '689'].includes(prefix)) {
    return { emoji: '⭐', label: '科创板', type: 'warning' }
  }
  // 创业板
  if (['300', '301'].includes(prefix)) {
    return { emoji: '🚀', label: '创业板', type: 'success' }
  }
  // 北交所
  if (
    prefix.startsWith('8') ||
    ['430', '831', '832', '833', '834', '835', '836', '837', '838', '839', '870', '871', '872', '873'].includes(prefix)
  ) {
    return { emoji: '🏢', label: '北交所', type: 'danger' }
  }
  // 主板
  return { emoji: '🏛️', label: '主板', type: 'info' }
}

const boardFilters = [
  { text: '⭐ 科创板', value: '科创板' },
  { text: '🚀 创业板', value: '创业板' },
  { text: '🏢 北交所', value: '北交所' },
  { text: '🏛️ 主板', value: '主板' },
]

const filterBoard = (value, row) => {
  return row.boardType?.label === value
}

const tableRows = computed(() => {
  const rows = Object.values(stocksMap.value)
  return rows.map((r) => {
    const hitCount = [r.rsi12, r.ma10, r.ma2560].filter(Boolean).length
    const priceInfo = priceMap.value[r.ts_code]
    return {
      ...r,
      name: nameMap.value[r.ts_code] || '',
      hitCount,
      boardType: getBoardType(r.ts_code),
      change_pct: priceInfo?.change_pct ?? r.pct_chg ?? null,
    }
  })
})

const fetchPriceMap = async () => {
  try {
    const resp = await watchlistApi.getAllWatchlistStocks({ page: 1, page_size: 1000 })
    const list = resp?.data || []
    const arr = Array.isArray(list) ? list : (list.stocks || [])
    const map = {}
    for (const item of arr) {
      if (item.ts_code) {
        map[item.ts_code] = {
          close_price: item.close_price ?? null,
          change_pct: item.change_pct ?? null,
        }
      }
    }
    priceMap.value = map
  } catch (e) {
    console.error('Failed to load watchlist prices:', e)
  }
}

const fetchNameMap = async () => {
  try {
    const resp = await watchlistApi.getAllWatchlistStocks({ page: 1, page_size: 1000 })
    const list = resp?.data?.stocks || resp?.data || []
    const map = {}
    const arr = Array.isArray(list) ? list : (list.stocks || [])
    for (const item of arr) {
      if (item.ts_code) {
        map[item.ts_code] = item.name || item.symbol || ''
      }
    }
    nameMap.value = map
  } catch (e) {
    console.error('Failed to load watchlist names:', e)
  }
}

const fetchLast = async () => {
  try {
    const resp = await indicatorCalcApi.getLast()
    summary.value = resp?.data || null
  } catch (e) {
    console.error('Failed to load last calc summary:', e)
  }
}

const fetchAll = async () => {
  loading.value = true
  try {
    const resp = await indicatorCalcApi.getAll()
    if (resp?.success) {
      stocksMap.value = resp?.data?.stocks || {}
    } else {
      stocksMap.value = {}
    }
  } catch (e) {
    console.error('Failed to load indicator cache:', e)
    stocksMap.value = {}
  } finally {
    loading.value = false
  }
}

const handleCompute = async () => {
  computing.value = true
  try {
    const resp = await indicatorCalcApi.compute()
    if (resp?.success) {
      summary.value = resp?.data || summary.value
      ElMessage.success('指标批量计算完成')
      await fetchAll()
    } else {
      ElMessage.error(resp?.error || '计算失败')
    }
  } catch (e) {
    console.error('Compute failed:', e)
    ElMessage.error('计算失败: ' + (e?.message || e))
  } finally {
    computing.value = false
  }
}

const goDetail = (tsCode) => {
  const url = router.resolve(`/stock/${tsCode}`).href
  window.open(url, '_blank')
}

const rowClassName = ({ row }) => {
  if (row.hitCount >= 3) return 'row-hit-strong'
  if (row.hitCount === 2) return 'row-hit-medium'
  return ''
}

const getChangeClass = (changePct) => {
  if (changePct > 0) return 'up'
  if (changePct < 0) return 'down'
  return 'flat'
}

const handleSortChange = () => {}

const sortByChangePct = (a, b) => {
  const av = a.change_pct ?? Number.NEGATIVE_INFINITY
  const bv = b.change_pct ?? Number.NEGATIVE_INFINITY
  return av - bv
}

const formatTime = (iso) => {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}

const formatDuration = (sec) => {
  if (sec == null) return '—'
  if (sec < 60) return `${sec.toFixed(1)} 秒`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m} 分 ${s} 秒`
}

onMounted(async () => {
  await Promise.all([fetchLast(), fetchNameMap(), fetchPriceMap()])
  if (summary.value) {
    await fetchAll()
  }
})
</script>

<style scoped>
.page-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.summary-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 12px;
  color: #909399;
}

.summary-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.summary-value.small {
  font-size: 13px;
  font-weight: 400;
}

.summary-value.hit {
  color: #67c23a;
}

.muted {
  color: #c0c4cc;
}

.hit-badge {
  display: inline-block;
  min-width: 28px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 13px;
  text-align: center;
}

.hit-0 {
  background: #f4f4f5;
  color: #909399;
}

.hit-1 {
  background: #e9e9eb;
  color: #909399;
}

.hit-2 {
  background: #fdf6ec;
  color: #e6a23c;
}

.hit-3 {
  background: #fef0f0;
  color: #f56c6c;
}

:deep(.row-hit-strong) {
  background-color: #fef9f0 !important;
}

:deep(.row-hit-medium) {
  background-color: #fdfbf7 !important;
}

.change-text {
  font-weight: 600;
}

.up {
  color: #f56c6c;
}

.down {
  color: #67c23a;
}
</style>
