<template>
  <div class="strategy-stock-picker">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>策略选股</span>
        </div>
      </template>

      <el-form :inline="true" @submit.prevent="handleExecute">
        <el-form-item label="选择日期">
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item label="选择策略">
          <el-select
            v-model="selectedStrategy"
            placeholder="选择策略"
            style="width: 280px"
          >
            <el-option
              v-for="strategy in strategies"
              :key="strategy.key"
              :label="strategy.name"
              :value="strategy.key"
            >
              <div class="strategy-option">
                <span class="strategy-name">{{ strategy.name }}</span>
                <span class="strategy-desc">{{ strategy.description }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            :disabled="!selectedStrategy || !selectedDate"
            @click="handleExecute"
          >
            执行选股
          </el-button>
        </el-form-item>
      </el-form>

      <el-alert
        v-if="selectedStrategyInfo"
        :title="selectedStrategyInfo.name"
        :description="selectedStrategyInfo.description"
        type="info"
        :closable="false"
        class="strategy-info"
      />
    </el-card>

    <el-card v-if="taskStatus && !executionResult" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>任务状态</span>
          <div class="header-actions">
            <el-tag :type="taskStatus.status === 'pending' ? 'warning' : 'primary'">
              {{ taskStatus.status === 'pending' ? '等待中' : '执行中' }}
            </el-tag>
          </div>
        </div>
      </template>
      <div class="task-status-info">
        <p><strong>任务ID:</strong> {{ taskStatus.task_id }}</p>
        <p><strong>策略:</strong> {{ taskStatus.strategy }}</p>
        <p><strong>状态:</strong> {{ taskStatus.status }}</p>
        <el-progress :percentage="taskStatus.status === 'pending' ? 30 : 60" :indeterminate="true" />
      </div>
    </el-card>

    <el-card v-if="executionResult" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>执行结果</span>
          <div class="header-actions">
            <el-tag :type="executionResult.success ? 'success' : 'danger'">
              {{ executionResult.success ? '成功' : '失败' }}
            </el-tag>
          </div>
        </div>
      </template>

      <div v-if="!executionResult.success" class="error-section">
        <el-alert
          :title="executionResult.error || '执行失败'"
          type="error"
          :closable="false"
        />
      </div>

      <div v-if="parsedData && parsedData.length > 0" class="result-section">
        <div class="result-summary">
          共筛选出 <strong>{{ parsedData.length }}</strong> 只股票
        </div>
        <el-table
          :data="parsedData"
          style="width: 100%"
          stripe
          border
          :max-height="600"
        >
          <el-table-column prop="ts_code" label="股票代码" width="130" fixed="left">
            <template #default="{ row }">
              <a
                :href="getXueqiuUrl(row.ts_code)"
                target="_blank"
                class="stock-link"
              >
                {{ row.ts_code }}
              </a>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="名称" width="120" fixed="left" />
          <el-table-column prop="industry" label="行业" width="120" />
          <el-table-column prop="close" label="收盘价" width="110" align="right">
            <template #default="{ row }">
              {{ formatPrice(row.close || row['close_T+0']) }}
            </template>
          </el-table-column>
          <el-table-column prop="pct_chg" label="涨跌幅" width="110" align="right">
            <template #default="{ row }">
              <span :class="getChangeClass(row.pct_chg || row['pct_chg_T+0'])">
                {{ formatPct(row.pct_chg || row['pct_chg_T+0']) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="T+1涨幅" width="120" align="right">
            <template #default="{ row }">
              <span :class="getChangeClass(row['change_T+1'])">
                {{ formatPct(row['change_T+1']) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="T+3涨幅" width="120" align="right">
            <template #default="{ row }">
              <span :class="getChangeClass(row['change_T+3'])">
                {{ formatPct(row['change_T+3']) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="T+7涨幅" width="120" align="right">
            <template #default="{ row }">
              <span :class="getChangeClass(row['change_T+7'])">
                {{ formatPct(row['change_T+7']) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="T+30涨幅" width="120" align="right">
            <template #default="{ row }">
              <span :class="getChangeClass(row['change_T+30'])">
                {{ formatPct(row['change_T+30']) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            v-for="col in dynamicColumns"
            :key="col.prop"
            :prop="col.prop"
            :label="col.label"
            :width="col.width || 140"
            align="right"
          >
            <template #default="{ row }">
              <span v-if="col.prop.includes('change_T+')" :class="getChangeClass(row[col.prop])">
                {{ formatPct(row[col.prop]) }}
              </span>
              <span v-else-if="col.prop.includes('pct_chg')" :class="getChangeClass(row[col.prop])">
                {{ formatPct(row[col.prop]) }}
              </span>
              <span v-else-if="col.prop.includes('close')">
                {{ formatPrice(row[col.prop]) }}
              </span>
              <span v-else>
                {{ row[col.prop] }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="executionResult.success" class="no-data">
        <el-empty description="未筛选出符合条件的股票" />
      </div>

      <el-collapse v-if="executionResult.stdout" class="mt-20">
        <el-collapse-item title="原始输出">
          <pre class="raw-output">{{ executionResult.stdout }}</pre>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { strategyApi, realtimeApi } from '@/api'
import { ElMessage } from 'element-plus'

const strategies = ref([])
const selectedStrategy = ref('')
const selectedDate = ref('')
const loading = ref(false)
const executionResult = ref(null)
const parsedData = ref(null)
const taskId = ref(null)
const taskStatus = ref(null)
const pollTimer = ref(null)

const getTodayDate = () => {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

const clearPolling = () => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

const enrichWithStockData = async (strategyData) => {
  if (!strategyData || strategyData.length === 0) return

  const tsCodes = strategyData.map(item => item.ts_code).filter(Boolean)
  if (tsCodes.length === 0) return

  try {
    const result = await realtimeApi.queryByDate(tsCodes, selectedDate.value, [1, 3, 7, 30])
    if (!result.success || !result.data) return

    const stockDataMap = new Map(result.data.map(item => [item.ts_code, item]))

    const enriched = strategyData.map(strategyItem => {
      const stockItem = stockDataMap.get(strategyItem.ts_code) || {}
      return {
        ...stockItem,
        ...strategyItem,
        ts_code: strategyItem.ts_code,
        name: strategyItem.name || stockItem.name || strategyItem.ts_code,
        industry: strategyItem.industry || stockItem.industry || '',
      }
    })

    parsedData.value = enriched
  } catch (error) {
    console.error('Enrich stock data failed:', error)
    ElMessage.warning('获取股票详细数据失败，仅显示策略结果')
  }
}

const pollTaskStatus = async () => {
  if (!taskId.value) return
  try {
    const response = await strategyApi.getTaskStatus(taskId.value)
    if (!response.success) {
      clearPolling()
      loading.value = false
      ElMessage.error(response.error || '查询任务状态失败')
      return
    }

    taskStatus.value = response

    if (response.status === 'completed') {
      clearPolling()
      loading.value = false
      executionResult.value = response
      if (response.data && Array.isArray(response.data) && response.data.length > 0) {
        await enrichWithStockData(response.data)
        const count = parsedData.value ? parsedData.value.length : 0
        ElMessage.success(`选股完成，共找到 ${count} 只股票`)
      } else {
        parsedData.value = response.data || []
        ElMessage.info('未筛选出符合条件的股票')
      }
    } else if (response.status === 'failed') {
      clearPolling()
      loading.value = false
      executionResult.value = response
      ElMessage.error(response.error || '执行失败')
    }
    // pending / running 状态继续轮询
  } catch (error) {
    console.error('Poll task status failed:', error)
    clearPolling()
    loading.value = false
    ElMessage.error('查询任务状态失败')
  }
}

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const selectedStrategyInfo = computed(() => {
  if (!selectedStrategy.value) return null
  return strategies.value.find(s => s.key === selectedStrategy.value)
})

const dynamicColumns = computed(() => {
  if (!parsedData.value || parsedData.value.length === 0) return []
  const firstRow = parsedData.value[0]
  const excludeKeys = [
    'ts_code', 'name', 'industry', 'close', 'pct_chg',
    'close_T+0', 'pct_chg_T+0',
    'change_T+1', 'change_T+3', 'change_T+7', 'change_T+30',
    'date_T+0', 'date_T+1', 'date_T+3', 'date_T+7', 'date_T+30',
  ]
  const columns = []
  for (const key of Object.keys(firstRow)) {
    if (excludeKeys.includes(key)) continue
    if (key.startsWith('close_T+') || key.startsWith('pct_chg_T+') || key.startsWith('change_T+')) continue
    if (key.startsWith('date_T+')) continue
    columns.push({
      prop: key,
      label: formatColumnLabel(key),
      width: getColumnWidth(key),
    })
  }
  return columns
})

const formatColumnLabel = (key) => {
  const labelMap = {
    'ma20': 'MA20',
    'ma25': 'MA25',
    'ma30': 'MA30',
    'ma60': 'MA60',
    'rsi12': 'RSI12',
    'volume': '成交量',
    'vol_ma5': '5日均量',
    'vol_ratio': '量比',
    'turnover': '换手率',
    'pe': '市盈率',
    'pb': '市净率',
    'market_cap': '总市值',
    'close_T+0': 'T日收盘',
    'pct_chg_T+0': 'T日涨幅',
    'change_T+1': 'T+1涨幅',
    'change_T+3': 'T+3涨幅',
    'change_T+7': 'T+7涨幅',
    'change_T+30': 'T+30涨幅',
    'score': '评分',
    'strategies': '策略',
    'rank': '排名',
    'min_rsi': '最低RSI',
    'max_rsi': '最高RSI',
    'avg_rsi': '平均RSI',
  }
  return labelMap[key] || key
}

const getColumnWidth = (key) => {
  if (key.includes('ma')) return 110
  if (key.includes('vol')) return 130
  if (key.includes('rsi')) return 110
  if (key.startsWith('change_T+')) return 120
  if (key === 'close_T+0') return 110
  if (key === 'pct_chg_T+0') return 110
  if (key === 'score') return 100
  if (key === 'strategies') return 150
  return 140
}

const loadStrategies = async () => {
  try {
    const response = await strategyApi.getStrategies()
    if (response.data) {
      strategies.value = response.data
    }
  } catch (error) {
    console.error('Failed to load strategies:', error)
    ElMessage.error('加载策略列表失败')
  }
}

const handleExecute = async () => {
  if (!selectedStrategy.value) {
    ElMessage.warning('请选择策略')
    return
  }
  if (!selectedDate.value) {
    ElMessage.warning('请选择日期')
    return
  }

  loading.value = true
  executionResult.value = null
  parsedData.value = null
  taskStatus.value = null
  clearPolling()

  try {
    const response = await strategyApi.executeStrategy({
      strategy: selectedStrategy.value,
      date: selectedDate.value,
      output: 'json',
    })

    if (response.success && response.task_id) {
      taskId.value = response.task_id
      ElMessage.info('策略已提交，正在执行中...')
      // 立即查询一次，然后开始轮询
      await pollTaskStatus()
      if (taskStatus.value && ['pending', 'running'].includes(taskStatus.value.status)) {
        pollTimer.value = setInterval(pollTaskStatus, 2000)
      }
    } else {
      loading.value = false
      ElMessage.error(response.error || '提交任务失败')
    }
  } catch (error) {
    console.error('Execute failed:', error)
    loading.value = false
    ElMessage.error('执行失败: ' + (error.response?.data?.detail || error.message))
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
  if (val > 0) return 'up'
  if (val < 0) return 'down'
  return 'flat'
}

const getXueqiuUrl = (tsCode) => {
  return `/stock/${tsCode}`
}

onMounted(() => {
  selectedDate.value = getTodayDate()
  loadStrategies()
})

onUnmounted(() => {
  clearPolling()
})
</script>

<style scoped>
.strategy-stock-picker {
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

.strategy-option {
  display: flex;
  flex-direction: column;
}

.strategy-name {
  font-weight: 500;
}

.strategy-desc {
  font-size: 12px;
  color: #909399;
}

.strategy-info {
  margin-top: 16px;
}

.result-summary {
  margin-bottom: 16px;
  font-size: 16px;
  color: #303133;
}

.up {
  color: #f56c6c;
}

.down {
  color: #67c23a;
}

.flat {
  color: #909399;
}

.stock-link {
  color: #409eff;
  text-decoration: none;
}

.stock-link:hover {
  text-decoration: underline;
}

.raw-output {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.5;
}

.no-data {
  padding: 40px 0;
}

.error-section {
  margin-bottom: 16px;
}

.task-status-info {
  padding: 16px;
}

.task-status-info p {
  margin: 0 0 12px 0;
  color: #606266;
}

.task-status-info p:last-child {
  margin-bottom: 16px;
}
</style>
