<template>
  <div class="stock-query">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>股票价格查询</span>
          <div class="header-actions">
            <el-button size="small" @click="openConfigDialog">
              配置
            </el-button>
            <span v-if="selectedDays.length" class="config-summary">
              当前: {{ selectedDays.map(d => 'T+' + d).join(', ') }}
            </span>
          </div>
        </div>
      </template>

      <el-form :inline="true" @submit.prevent="handleQuery">
        <el-form-item label="股票代码">
          <el-input
            v-model="tsCodesInput"
            type="textarea"
            :rows="3"
            placeholder="输入股票代码，支持逗号或换行分隔&#10;例如: 600000.SH, 000001.SZ&#10;或: 600000&#10;     000001"
            style="width: 400px"
          />
        </el-form-item>
        <el-form-item label="查询日期">
          <el-date-picker
            v-model="queryDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleQuery">
            查询
          </el-button>
        </el-form-item>
      </el-form>
      <div v-if="queryHistory.length" class="query-history">
        <div class="history-label">查询记录：</div>
        <div class="history-list">
          <el-tag
            v-for="record in displayedHistory"
            :key="record.id"
            class="history-tag"
            closable
            @click="applyHistory(record)"
            @close="deleteHistory(record)"
          >
            {{ record.date }} ({{ record.codes.length }}只)
          </el-tag>
          <el-button
            v-if="queryHistory.length > 3"
            size="small"
            text
            type="primary"
            @click="openHistoryDialog"
          >
            更多
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card v-if="queryResult" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>查询结果</span>
          <div class="trading-dates" v-if="tradingDates">
            <el-tag size="small" type="info">T日: {{ tradingDates['T+0'] }}</el-tag>
            <el-tag
              v-for="day in selectedDays"
              :key="day"
              size="small"
            >
              T+{{ day }}: {{ tradingDates['T+' + day] }}
            </el-tag>
          </div>
        </div>
      </template>

      <el-table
        :data="queryResult"
        style="width: 100%"
        stripe
        border
        :row-class-name="getRowClassName"
        @row-click="handleRowClick"
      >
        <el-table-column label="股票代码" width="130" fixed>
          <template #default="{ row }">
            <a
              :href="getXueqiuUrl(row.ts_code)"
              target="_blank"
              class="stock-link"
              @click.stop="selectRow(row)"
            >
              {{ row.ts_code }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="100" fixed />
        <el-table-column prop="industry" label="板块" width="120" />

        <el-table-column label="T日收盘" width="110" align="right">
          <template #default="{ row }">
            {{ formatPrice(row['close_T+0']) }}
          </template>
        </el-table-column>

        <el-table-column
          v-for="day in selectedDays"
          :key="day"
          :label="'T+' + day + ' 涨幅'"
          width="110"
          align="right"
        >
          <template #default="{ row }">
            <span :class="getChangeClass(row['change_T+' + day])">
              {{ formatPct(row['change_T+' + day]) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click.stop="openFollowDialog(row)"
            >
              关注
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click.stop="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="configDialogVisible"
      title="查询配置"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="T+N 天数">
          <el-select
            v-model="configDays"
            multiple
            allow-create
            filterable
            default-first-option
            placeholder="选择或输入天数"
            style="width: 220px"
          >
            <el-option
              v-for="day in dayOptions"
              :key="day"
              :label="'T+' + day"
              :value="day"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">
          确认
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="historyDialogVisible"
      title="查询历史记录"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-table :data="queryHistory" style="width: 100%" stripe border>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="date" label="查询日期" width="120" />
        <el-table-column prop="codes" label="股票代码">
          <template #default="{ row }">
            <el-tag
              v-for="(code, idx) in row.codes.slice(0, 5)"
              :key="idx"
              size="small"
              class="code-tag"
            >
              {{ code }}
            </el-tag>
            <span v-if="row.codes.length > 5" class="more-codes">
              +{{ row.codes.length - 5 }} 只
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="applyHistory(row); historyDialogVisible = false"
            >
              应用
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="deleteHistory(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog
      v-model="followDialogVisible"
      title="关注股票"
      width="450px"
      :close-on-click-modal="false"
    >
      <div v-if="currentFollowStock" class="follow-dialog-content">
        <div class="stock-basic-info">
          <h4>股票信息</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="股票代码">
              {{ currentFollowStock.ts_code }}
            </el-descriptions-item>
            <el-descriptions-item label="名称">
              {{ currentFollowStock.name }}
            </el-descriptions-item>
            <el-descriptions-item label="板块">
              {{ currentFollowStock.industry || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="当前价格">
              ¥{{ formatPrice(currentFollowStock['close_T+0']) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="follow-form">
          <h4>关注设置</h4>
          <el-form :model="followForm" label-width="100px">
            <el-form-item label="关注原因">
              <el-select
                v-model="followForm.watch_reason"
                placeholder="请选择关注原因"
                style="width: 100%"
              >
                <el-option
                  v-for="reason in watchReasons"
                  :key="reason.value"
                  :label="reason.label"
                  :value="reason.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="关注日期">
              <el-date-picker
                v-model="followForm.watch_date"
                type="date"
                placeholder="选择关注日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disabledDate"
                style="width: 100%"
              />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <template #footer>
        <el-button @click="followDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="followLoading"
          @click="confirmFollow"
        >
          确认关注
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { realtimeApi, watchlistApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const tsCodesInput = ref('')
const queryDate = ref('')
const loading = ref(false)
const queryResult = ref(null)
const tradingDates = ref(null)
const selectedRow = ref(null)

const selectedDays = ref([1, 3, 7, 30])
const dayOptions = ref([1, 2, 3, 4, 7, 15, 30])
const configDialogVisible = ref(false)
const configDays = ref([1, 3, 7, 30])
const DAYS_CONFIG_KEY = 'stock_query_days_config'

const openConfigDialog = () => {
  configDays.value = [...selectedDays.value]
  configDialogVisible.value = true
}

const saveConfig = () => {
  const sorted = [...configDays.value].sort((a, b) => a - b)
  selectedDays.value = sorted
  localStorage.setItem(DAYS_CONFIG_KEY, JSON.stringify(sorted))
  configDialogVisible.value = false
}

const loadDaysConfig = () => {
  const stored = localStorage.getItem(DAYS_CONFIG_KEY)
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed) && parsed.length) {
        selectedDays.value = parsed
      }
    } catch (e) {
      console.error('Failed to load days config:', e)
    }
  }
}

const queryHistory = ref([])
const HISTORY_KEY = 'stock_query_history'
const MAX_HISTORY = 20
const historyDialogVisible = ref(false)

const displayedHistory = computed(() => {
  return queryHistory.value.slice(0, 3)
})

const openHistoryDialog = () => {
  historyDialogVisible.value = true
}

const followDialogVisible = ref(false)
const followLoading = ref(false)
const currentFollowStock = ref(null)
const followForm = ref({
  watch_reason: '',
  watch_date: ''
})
const watchReasons = ref([])

const getTodayDate = () => {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const saveQueryHistory = (codes, date) => {
  const record = {
    id: Date.now(),
    codes: [...codes],
    date,
    timestamp: new Date().toISOString()
  }
  const existing = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  const filtered = existing.filter(
    item => !(item.date === date && item.codes.join(',') === codes.join(','))
  )
  const updated = [record, ...filtered].slice(0, MAX_HISTORY)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(updated))
  queryHistory.value = updated
}

const loadQueryHistory = () => {
  const stored = localStorage.getItem(HISTORY_KEY)
  if (stored) {
    queryHistory.value = JSON.parse(stored)
  }
}

const applyHistory = (record) => {
  tsCodesInput.value = record.codes.join('\n')
  queryDate.value = record.date
  handleQuery()
}

const deleteHistory = (record) => {
  queryHistory.value = queryHistory.value.filter(item => item.id !== record.id)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(queryHistory.value))
}

const handleQuery = async () => {
  const codes = tsCodesInput.value
    .split(/[,，\n\t\s]+/)
    .map(c => c.trim())
    .filter(c => c)

  if (!codes.length) {
    ElMessage.warning('请输入至少一个股票代码')
    return
  }

  if (!queryDate.value) {
    ElMessage.warning('请选择查询日期')
    return
  }

  loading.value = true
  try {
    const result = await realtimeApi.queryByDate(codes, queryDate.value, selectedDays.value)
    queryResult.value = result.data || []
    tradingDates.value = result.trading_dates || null

    if (!queryResult.value.length) {
      ElMessage.info('未查询到数据')
    } else {
      saveQueryHistory(codes, queryDate.value)
    }
  } catch (error) {
    console.error('Query failed:', error)
    ElMessage.error('查询失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const formatPrice = (price) => {
  if (price === null || price === undefined) return '-'
  return Number(price).toFixed(2)
}

const formatPct = (pct) => {
  if (pct === null || pct === undefined) return '-'
  const val = Number(pct)
  return (val > 0 ? '+' : '') + val.toFixed(2) + '%'
}

const getChangeClass = (val) => {
  if (val === null || val === undefined) return ''
  return val > 0 ? 'up' : val < 0 ? 'down' : ''
}

const getXueqiuUrl = (tsCode) => {
  // ts_code 格式: 002342.SZ → 雪球格式: SZ002342
  const [code, exchange] = tsCode.split('.')
  //return `https://xueqiu.com/S/${exchange}${code}`
  return `/stock/${tsCode}`
}

const selectRow = (row) => {
  selectedRow.value = row
}

const handleRowClick = (row) => {
  selectedRow.value = row
}

const getRowClassName = ({ row }) => {
  if (selectedRow.value && row.ts_code === selectedRow.value.ts_code) {
    return 'selected-row'
  }
  return ''
}

onMounted(() => {
  loadQueryHistory()
  loadDaysConfig()
})

const loadWatchReasons = async () => {
  try {
    const response = await watchlistApi.getWatchReasons(8)
    if (response.data?.watch_reasons) {
      watchReasons.value = response.data.watch_reasons
    }
  } catch (error) {
    console.error('Failed to load watch reasons:', error)
  }
}

const openFollowDialog = async (row) => {
  currentFollowStock.value = row
  followForm.value = {
    watch_reason: '',
    watch_date: getTodayDate()
  }
  await loadWatchReasons()
  followDialogVisible.value = true
}

const confirmFollow = async () => {
  if (!followForm.value.watch_reason) {
    ElMessage.warning('请选择关注原因')
    return
  }

  followLoading.value = true
  try {
    await watchlistApi.addStock(8, {
      ts_code: currentFollowStock.value.ts_code,
      watch_reason: followForm.value.watch_reason,
      watch_date: followForm.value.watch_date
    })
    ElMessage.success(`已将 ${currentFollowStock.value.name} (${currentFollowStock.value.ts_code}) 添加到关注列表`)
    followDialogVisible.value = false
  } catch (error) {
    console.error('Follow failed:', error)
    ElMessage.error('关注失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    followLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.name} (${row.ts_code}) 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    queryResult.value = queryResult.value.filter(
      (item) => item.ts_code !== row.ts_code
    )

    if (selectedRow.value?.ts_code === row.ts_code) {
      selectedRow.value = null
    }

    ElMessage.success('已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.stock-query {
  padding: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trading-dates {
  display: flex;
  gap: 8px;
}

.up {
  color: #f56c6c;
  font-weight: 500;
}

.down {
  color: #67c23a;
  font-weight: 500;
}

.stock-link {
  color: #409eff;
  text-decoration: none;
}

.stock-link:hover {
  text-decoration: underline;
}
:deep(.selected-row) {
  background-color: #e6f7ff !important;
}

:deep(.selected-row:hover > td) {
  background-color: #e6f7ff !important;
}

.follow-dialog-content {
  padding: 0 10px;
}

.stock-basic-info {
  margin-bottom: 24px;
}

.stock-basic-info h4,
.follow-form h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
  border-left: 4px solid #409eff;
  padding-left: 8px;
}

.follow-form {
  margin-top: 20px;
}

.query-history {
  margin-top: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.history-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
  line-height: 32px;
}

.history-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-tag {
  cursor: pointer;
}

.history-tag:hover {
  background-color: #ecf5ff;
}

.config-summary {
  margin-left: 8px;
  font-size: 13px;
  color: #909399;
}

.code-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.more-codes {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}
</style>
