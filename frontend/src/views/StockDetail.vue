<template>
  <div>
    <div class="stock-detail" v-if="stock">
      <el-page-header @back="$router.back()" :content="stock.name" />

      <el-row :gutter="20" class="mt-20">
        <el-col :span="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>{{ stock.ts_code }} - K线图</span>
                <el-radio-group v-model="klinePeriod" size="small" @change="loadKline">
                  <el-radio-button label="daily">日线</el-radio-button>
                  <el-radio-button label="weekly">周线</el-radio-button>
                  <el-radio-button label="monthly">月线</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            
            <StockKlineChart
              ref="klineChartRef"
              :tsCode="props.tsCode"
              :stockName="stock?.name"
              :klineData="klineData"
              :showMACD="true"
              minHeight="400px"
              style="height: 400px;"
            />
          </el-card>

          <!-- 信号时间线 -->
          <el-card class="mt-20 signal-timeline-card" v-loading="signalsLoading">
            <template #header>
              <div class="card-header">
                <span>信号记录</span>
                <div class="header-actions">
                  <span class="signal-count" v-if="signalList.length > 0">共 {{ signalList.length }} 条</span>
                  <el-button size="small" type="primary" link @click="openAddNoteDialog">
                    <el-icon><EditPen /></el-icon>备注
                  </el-button>
                </div>
              </div>
            </template>

            <div v-if="signalList.length === 0" class="empty-signals">
              <el-empty description="暂无信号记录" :image-size="60" />
            </div>

            <el-timeline v-else>
              <el-timeline-item
                v-for="signal in signalList"
                :key="signal.id"
                :type="getSignalTimelineType(signal.signal_type)"
                :timestamp="formatDateTime(signal.created_at || signal.signal_date)"
                placement="top"
              >
                <div class="signal-timeline-content">
                  <div class="signal-timeline-header">
                    <el-tag size="small" :type="getSignalType(signal.signal_type)">
                      {{ formatSignal(signal.signal_type) }}
                    </el-tag>
                    <span v-if="signal.signal_strength" class="signal-strength">
                      强度: {{ signal.signal_strength }}
                    </span>
                  </div>

                  <!-- NOTE 类型展示 note_content -->
                  <div v-if="signal.signal_type === 'NOTE'" class="signal-note">
                    {{ signal.note_content || '无内容' }}
                  </div>

                  <!-- 其他类型展示 execution_result -->
                  <div v-else class="signal-result">
                    <div v-if="signal.execution_result" class="result-text">
                      {{ signal.execution_result }}
                    </div>
                    <div v-else class="result-empty">
                      信号产生时价格: ¥{{ signal.current_price?.toFixed(2) || '-' }}
                    </div>
                  </div>

                  <div v-if="signal.indicators" class="signal-indicators-mini">
                    <el-tag size="small" type="info" v-if="signal.indicators.ma20">
                      MA20: {{ signal.indicators.ma20.toFixed(2) }}
                    </el-tag>
                    <el-tag size="small" type="info" v-if="signal.indicators.macd">
                      MACD: {{ signal.indicators.macd.toFixed(2) }}
                    </el-tag>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card v-loading="moneyflowLoading">
            <template #header>
              <div class="card-header">
                <span>资金流向</span>
                <div class="moneyflow-legend">
                  <el-checkbox v-model="showLargeOnly" size="small">仅大单</el-checkbox>
                  <span class="legend-item"><span class="dot red"></span>正向</span>
                  <span class="legend-item"><span class="dot green"></span>负向</span>
                </div>
              </div>
            </template>
            <div ref="moneyflowChart" style="height: 300px;"></div>
          </el-card>

          <el-card class="mt-20">
            <template #header>
              <div class="card-header">
                <span>实时行情</span>
                <el-button size="small" type="primary" link @click="openXueqiu(stock)">
                  雪球
                </el-button>
              </div>
            </template>

            <div class="price-display">
              <div class="current-price">
                ¥{{ stock.current_price?.toFixed(2) }}
              </div>
              <div 
                class="change-pct"
                :class="getChangeClass(stock.change_pct)"
              >
                {{ stock.change_pct > 0 ? '+' : '' }}{{ stock.change_pct?.toFixed(2) }}%
              </div>
            </div>

            <el-divider />

            <div class="info-grid">
              <div class="info-item">
                <span class="label">成交量:</span>
                <span>{{ formatVolume(stock.volume) }}</span>
              </div>
              <div class="info-item">
                <span class="label">成交额:</span>
                <span>{{ formatAmount(stock.amount) }}</span>
              </div>
              <div class="info-item">
                <span class="label">换手率:</span>
                <span>{{ stock.turnover_rate?.toFixed(2) }}%</span>
              </div>
              <div class="info-item">
                <span class="label">市盈率:</span>
                <span>{{ stock.pe?.toFixed(2) || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">市净率:</span>
                <span>{{ stock.pb?.toFixed(2) || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">总市值:</span>
                <span>{{ formatMarketCap(stock.market_cap) }}</span>
              </div>
            </div>
          </el-card>

          <el-card class="mt-20" v-if="latestSignal">
            <template #header>
              <div class="card-header">
                <span>最新信号</span>
                <el-tag :type="getSignalType(latestSignal.signal_type)">
                  {{ formatSignal(latestSignal.signal_type) }}
                </el-tag>
              </div>
            </template>

            <div class="signal-details">
              <div class="signal-item">
                <span class="label">信号强度:</span>
                <el-rate
                  v-model="latestSignal.signal_strength"
                  disabled
                  show-score
                  :max="5"
                />
              </div>

              <div class="signal-item" v-if="latestSignal.indicators">
                <span class="label">技术指标:</span>
                <div class="indicators">
                  <el-tag size="small">MA20: {{ latestSignal.indicators.ma20?.toFixed(2) }}</el-tag>
                  <el-tag size="small">MACD: {{ latestSignal.indicators.macd?.toFixed(2) }}</el-tag>
                  <el-tag size="small">KDJ-J: {{ latestSignal.indicators.kdj_j?.toFixed(2) }}</el-tag>
                  <el-tag size="small">RSI: {{ latestSignal.indicators.rsi14?.toFixed(2) }}</el-tag>
                </div>
              </div>

              <div class="signal-item">
                <span class="label">信号日期:</span>
                <span>{{ formatDate(latestSignal.signal_date) }}</span>
              </div>
            </div>
          </el-card>

        </el-col>
      </el-row>
    </div>

    <el-empty v-else description="加载中..." />

    <!-- 添加备注弹窗 -->
    <el-dialog v-model="showAddNoteDialog" title="添加股票备注" width="500px">
      <el-form label-width="80px">
        <el-form-item label="股票">
          <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="noteContentInput"
            type="textarea"
            :rows="4"
            placeholder="请输入备注内容..."
            resize="none"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddNoteDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveNote"
          :disabled="!noteContentInput.trim() || noteLoading"
          :loading="noteLoading"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { stockApi, signalApi, basicDataApi } from '@/api'
import { ElMessage } from 'element-plus'
import { EditPen } from '@element-plus/icons-vue'
import StockKlineChart from '@/components/StockKlineChart.vue'

const props = defineProps(['tsCode'])

const stock = ref(null)
const klineData = ref([])
const klinePeriod = ref('daily')
const latestSignal = ref(null)
const klineChartRef = ref(null)

const moneyflowLoading = ref(false)
const moneyflowData = ref([])
const showLargeOnly = ref(true)
const moneyflowChart = ref(null)
let moneyflowChartInstance = null

// 信号时间线数据
const signalsLoading = ref(false)
const signalList = ref([])

// 添加备注弹窗相关
const showAddNoteDialog = ref(false)
const noteContentInput = ref('')
const noteLoading = ref(false)

onMounted(() => {
  loadStockDetail()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (moneyflowChartInstance) {
    moneyflowChartInstance.dispose()
    moneyflowChartInstance = null
  }
})

const handleResize = () => {
  klineChartRef.value?.resize()
  if (moneyflowChartInstance) {
    moneyflowChartInstance.resize()
  }
}

const loadStockDetail = async () => {
  try {
    const response = await stockApi.getDetail(props.tsCode)
    stock.value = response.data

    await loadKline()
    await loadSignal()
    await loadMoneyflow()
    await loadSignals()
  } catch (error) {
    console.error('Failed to load stock detail:', error)
    ElMessage.error('加载失败')
  }
}

const loadMoneyflow = async () => {
  moneyflowLoading.value = true
  try {
    const response = await basicDataApi.getMoneyflow(props.tsCode, 20)
    if (response.success) {
      moneyflowData.value = response.data || []
      if (moneyflowData.value.length > 0) {
        renderMoneyflowChart()
      }
    } else {
      ElMessage.error(response.error || '获取资金流向失败')
    }
  } catch (error) {
    console.error('Failed to load moneyflow:', error)
  } finally {
    moneyflowLoading.value = false
  }
}

const renderMoneyflowChart = () => {
  if (!moneyflowChart.value || moneyflowData.value.length === 0) return

  if (!moneyflowChartInstance) {
    moneyflowChartInstance = echarts.init(moneyflowChart.value)
  }

  const data = moneyflowData.value
  const dates = data.map(item => item.trade_date)

  const smNet = data.map(item => +(item.buy_sm_amount - item.sell_sm_amount).toFixed(2))
  const mdNet = data.map(item => +(item.buy_md_amount - item.sell_md_amount).toFixed(2))
  const lgNet = data.map(item => +(item.buy_lg_amount - item.sell_lg_amount).toFixed(2))
  const elgNet = data.map(item => +(item.buy_elg_amount - item.sell_elg_amount).toFixed(2))

  const colorPos = '#f56c6c'
  const colorNeg = '#67c23a'
  const toBarData = (arr) => arr.map(v => ({ value: v, itemStyle: { color: v >= 0 ? colorPos : colorNeg } }))

  const series = []

  if (!showLargeOnly.value) {
    series.push(
      { name: '小单(<5万)', type: 'bar', stack: 'moneyflow', data: toBarData(smNet) },
      { name: '中单(5万-20万)', type: 'bar', stack: 'moneyflow', data: toBarData(mdNet) }
    )
  }

  series.push(
    { name: '大单(20万-100万)', type: 'bar', stack: 'moneyflow', data: toBarData(lgNet) },
    { name: '特大单(>=100万)', type: 'bar', stack: 'moneyflow', data: toBarData(elgNet) }
  )

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: false,
      appendToBody: true,
      className: 'moneyflow-tooltip',
      formatter: (params) => {
        let html = `<div style="font-weight:bold;margin-bottom:5px">${params[0].name}</div>`
        let total = 0
        params.forEach(p => {
          const val = p.value
          total += val
          const color = val >= 0 ? '#f56c6c' : '#67c23a'
          html += `<div>${p.marker} ${p.seriesName}: <span style="color:${color};font-weight:bold">${val >= 0 ? '+' : ''}${val.toFixed(2)}万</span></div>`
        })
        const totalColor = total >= 0 ? '#f56c6c' : '#67c23a'
        html += `<div style="margin-top:5px;border-top:1px solid #eee;padding-top:5px;font-weight:bold">净流入: <span style="color:${totalColor}">${total >= 0 ? '+' : ''}${total.toFixed(2)}万</span></div>`
        return html
      }
    },
    legend: { show: false },
    grid: {
      left: '8%',
      right: '4%',
      bottom: '15%',
      top: '40px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value) => value.substring(5),
        fontSize: 9,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => {
          if (Math.abs(value) >= 10000) return (value / 10000).toFixed(1) + '亿'
          return value + '万'
        },
        fontSize: 9
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#eee' }
      }
    },
    dataZoom: [{ type: 'inside', start: 0, end: 100 }],
    series: series
  }

  moneyflowChartInstance.setOption(option, true)
}

watch(showLargeOnly, () => {
  if (moneyflowData.value.length > 0) {
    renderMoneyflowChart()
  }
})

const loadKline = async () => {
  try {
    const response = await stockApi.getKline(props.tsCode, klinePeriod.value, 60)
    klineData.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load kline:', error)
  }
}

const loadSignal = async () => {
  try {
    const response = await signalApi.getLatest(props.tsCode)
    latestSignal.value = response.data
  } catch (error) {
    console.error('Failed to load signal:', error)
  }
}

const loadSignals = async () => {
  signalsLoading.value = true
  try {
    const response = await signalApi.getAll({
      ts_code: props.tsCode,
      active_only: false,
      limit: 100
    })
    if (response.success) {
      signalList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load signals:', error)
  } finally {
    signalsLoading.value = false
  }
}

const getChangeClass = (change) => {
  if (!change) return ''
  return change > 0 ? 'up' : change < 0 ? 'down' : ''
}

const getSignalType = (type) => {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'info', NOTE: 'warning' }
  return map[type] || 'info'
}

const getSignalTimelineType = (type) => {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'primary', NOTE: 'warning' }
  return map[type] || 'primary'
}

const formatSignal = (type) => {
  const map = { BUY: '买入', SELL: '卖出', WATCH: '观望', NOTE: '备注' }
  return map[type] || type
}

const formatVolume = (volume) => {
  if (!volume) return '-'
  if (volume > 100000000) return (volume / 100000000).toFixed(2) + '亿'
  if (volume > 10000) return (volume / 10000).toFixed(2) + '万'
  return volume.toString()
}

const formatAmount = (amount) => {
  if (!amount) return '-'
  if (amount > 100000000) return (amount / 100000000).toFixed(2) + '亿'
  if (amount > 10000) return (amount / 10000).toFixed(2) + '万'
  return amount.toString()
}

const formatMarketCap = (cap) => {
  if (!cap) return '-'
  return (cap / 100000000).toFixed(2) + '亿'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-')
}

// 打开雪球网
const openXueqiu = (stock) => {
  if (!stock || !stock.ts_code) return
  // 转换格式: 300006.SZ -> SZ300006
  const [code, exchange] = stock.ts_code.split('.')
  const xueqiuCode = exchange + code
  window.open(`https://xueqiu.com/S/${xueqiuCode}`, '_blank')
}

// 打开添加备注弹窗
const openAddNoteDialog = () => {
  noteContentInput.value = ''
  showAddNoteDialog.value = true
}

// 保存备注
const saveNote = async () => {
  if (!stock.value || !stock.value.ts_code || !noteContentInput.value.trim()) return

  noteLoading.value = true
  try {
    const response = await signalApi.addNote(
      stock.value.ts_code,
      noteContentInput.value.trim()
    )
    if (response.success) {
      ElMessage.success('备注添加成功')
      showAddNoteDialog.value = false
      // 刷新信号列表
      await loadSignals()
    } else {
      ElMessage.error(response.error || '添加备注失败')
    }
  } catch (error) {
    console.error('Failed to add note:', error)
    ElMessage.error('添加备注失败')
  } finally {
    noteLoading.value = false
  }
}
</script>

<style scoped>
.stock-detail {
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

.price-display {
  text-align: center;
  padding: 20px 0;
}

.current-price {
  font-size: 36px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.change-pct {
  font-size: 20px;
  font-weight: 500;
}

.change-pct.up {
  color: #f56c6c;
}

.change-pct.down {
  color: #67c23a;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
}

.info-item .label {
  color: #606266;
}

.signal-details {
  padding: 10px 0;
}

.signal-item {
  margin-bottom: 15px;
}

.signal-item .label {
  display: block;
  color: #606266;
  margin-bottom: 5px;
}

.indicators {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.moneyflow-legend {
  display: flex;
  align-items: center;
  gap: 12px;
}

.moneyflow-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.moneyflow-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.moneyflow-legend .dot.red {
  background-color: #f56c6c;
}

.moneyflow-legend .dot.green {
  background-color: #67c23a;
}

/* 信号时间线样式 */
.signal-timeline-card {
  max-height: 600px;
  overflow-y: auto;
}

.signal-count {
  font-size: 12px;
  color: #909399;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.empty-signals {
  padding: 20px 0;
}

.signal-timeline-content {
  padding: 8px 0;
}

.signal-timeline-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.signal-date {
  font-size: 12px;
  color: #909399;
}

.signal-strength {
  font-size: 12px;
  color: #606266;
}

.signal-note {
  padding: 10px 12px;
  background-color: #fdf6ec;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.signal-result {
  padding: 10px 12px;
  background-color: #f4f4f5;
  border-radius: 4px;
}

.result-text {
  color: #303133;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-empty {
  color: #909399;
  font-size: 13px;
  font-style: italic;
}

.signal-indicators-mini {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}

/* 资金流向 tooltip 层级 */
:global(.moneyflow-tooltip) {
  z-index: 9999 !important;
}
</style>
