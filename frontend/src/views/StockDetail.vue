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
              minHeight="400px"
              style="height: 400px;"
            />
          </el-card>

          <!-- 成交量 -->
          <el-card class="mt-20">
            <template #header>
              <div class="card-header">
                <span>成交量</span>
                <span class="volume-legend">
                  <span class="legend-item"><span class="dot" style="background-color:#f56c6c;"></span>阳线</span>
                  <span class="legend-item"><span class="dot" style="background-color:#67c23a;"></span>阴线</span>
                  <span class="legend-item"><span class="dot" style="background-color:#e6a23c;"></span>MA5量</span>
                </span>
              </div>
            </template>
            <StockVolumeChart
              ref="volumeChartRef"
              :klineData="klineData"
            />
          </el-card>

          <!-- MACD 指标 -->
          <el-card class="mt-20">
            <template #header>
              <div class="card-header">
                <span>MACD 指标</span>
                <span class="macd-legend">
                  <span class="legend-item"><span class="dot" style="background-color:#f5a623;"></span>DIF</span>
                  <span class="legend-item"><span class="dot" style="background-color:#5470c6;"></span>DEA</span>
                  <span class="legend-item"><span class="dot" style="background-color:#f56c6c;"></span>MACD柱</span>
                </span>
              </div>
            </template>
            <StockMacdChart
              ref="macdChartRef"
              :klineData="klineData"
            />
          </el-card>

          <!-- ADX 趋势强度指标 -->
          <el-card class="mt-20">
            <template #header>
              <div class="card-header">
                <span>ADX 趋势强度</span>
                <span class="adx-legend">
                  <span class="legend-item"><span class="dot" style="background-color:#ee6666;"></span>+DI</span>
                  <span class="legend-item"><span class="dot" style="background-color:#91cc75;"></span>-DI</span>
                  <span class="legend-item"><span class="dot" style="background-color:#5470c6;"></span>ADX</span>
                </span>
              </div>
            </template>
            <StockAdxChart
              ref="adxChartRef"
              :klineData="klineData"
            />
          </el-card>

          <!-- 信号时间线 -->
          <el-card class="mt-20 signal-timeline-card" v-loading="signalsLoading">
            <template #header>
              <div class="card-header">
                <span>信号记录</span>
                <div class="header-actions">
                  <span class="signal-count" v-if="signalList.length > 0">共 {{ signalList.length }} 条</span>
                  <el-button size="small" type="primary" link @click="openNotesDialog">
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
            <div class="moneyflow-summary" v-if="moneyflowSummary">
              <div class="summary-item">
                <span class="summary-label">20日净流入</span>
                <span class="summary-value" :class="moneyflowSummary.d20 >= 0 ? 'up' : 'down'">
                  {{ formatNetInflow(moneyflowSummary.d20) }}
                </span>
              </div>
              <div class="summary-item">
                <span class="summary-label">10日净流入</span>
                <span class="summary-value" :class="moneyflowSummary.d10 >= 0 ? 'up' : 'down'">
                  {{ formatNetInflow(moneyflowSummary.d10) }}
                </span>
              </div>
              <div class="summary-item">
                <span class="summary-label">5日净流入</span>
                <span class="summary-value" :class="moneyflowSummary.d5 >= 0 ? 'up' : 'down'">
                  {{ formatNetInflow(moneyflowSummary.d5) }}
                </span>
              </div>
            </div>
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

          <el-card class="mt-20" v-if="watchlistStockInfo">
            <template #header>
              <div class="card-header">
                <span>所属分组</span>
                <el-button size="small" type="primary" link @click="openSwitchGroupDialog">
                  换组
                </el-button>
              </div>
            </template>

            <div class="watchlist-info-grid">
              <div class="info-item">
                <span class="label">分组:</span>
                <span>{{ watchlistStockInfo.watchlist_name }}</span>
              </div>
              <div class="info-item" v-if="watchlistStockInfo.watch_date">
                <span class="label">关注日期:</span>
                <span>{{ watchlistStockInfo.watch_date }}</span>
              </div>
              <div class="info-item" v-if="watchlistStockInfo.notes">
                <span class="label">备注:</span>
                <span>{{ watchlistStockInfo.notes }}</span>
              </div>
            </div>
          </el-card>

          <el-card class="mt-20 indicator-guide-card">
            <template #header>
              <div class="card-header">
                <span>指标说明</span>
                <el-tag type="success" size="small">真突破（可关注）</el-tag>
              </div>
            </template>

            <div class="indicator-guide">
              <div class="guide-feature">
                均线多头，MACD金叉，大单流入，OBV新高，ADX走强
              </div>

              <div class="guide-section">
                <div class="guide-title">MA (5,10,20)</div>
                <div class="guide-text">5&gt;10&gt;20，股价沿5日线攀升。</div>
              </div>

              <div class="guide-section">
                <div class="guide-title">MACD</div>
                <div class="guide-text">DIF上穿DEA，红柱渐长，在零轴上方二次金叉。</div>
              </div>

              <div class="guide-section">
                <div class="guide-title">大单/DDX</div>
                <div class="guide-text">连续3日大单净流入，DDX红柱逐日放大（非脉冲）。</div>
              </div>

              <div class="guide-section">
                <div class="guide-title">OBV</div>
                <div class="guide-text">随股价创新高，OBV同步创120日新高。</div>
              </div>

              <div class="guide-section">
                <div class="guide-title">ADX</div>
                <div class="guide-text">从20升至35，+DI在-DI上方。</div>
              </div>

              <el-divider />

              <div class="guide-summary">
                <div class="summary-line">
                  <span class="summary-label">综合判断：</span>强趋势+资金健康+量价配合。
                </div>
                <div class="summary-line">
                  <span class="summary-label">操作：</span>沿5日线持有，ADX&gt;50且走平考虑减仓。
                </div>
              </div>
            </div>
          </el-card>

        </el-col>
      </el-row>
    </div>

    <el-empty v-else description="加载中..." />

    <!-- 编辑备注弹窗 -->
    <el-dialog v-model="showNotesDialog" title="编辑股票备注" width="500px">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            ref="notesInputRef"
            v-model="stockNotesInput"
            type="textarea"
            :rows="4"
            placeholder="请输入股票备注信息..."
            resize="none"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showNotesDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveStockNotes"
          :disabled="notesLoading"
          :loading="notesLoading"
        >
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 切换分组弹窗 -->
    <el-dialog v-model="showSwitchGroupDialog" title="切换分组" width="500px">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="当前分组">
          <el-text>{{ watchlistStockInfo?.watchlist_name }}</el-text>
        </el-form-item>
        <el-form-item label="目标分组" required>
          <el-select
            v-model="selectedTargetWatchlist"
            placeholder="选择目标分组"
            style="width: 100%"
          >
            <el-option
              v-for="wl in availableWatchlists"
              :key="wl.id"
              :label="wl.name"
              :value="wl.id"
              :disabled="wl.id === watchlistStockInfo?.watchlist_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="变更理由" required>
          <el-input
            v-model="switchGroupReason"
            type="textarea"
            :rows="3"
            placeholder="请填写变更理由（必填）"
            resize="none"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showSwitchGroupDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="switchStockGroup"
          :disabled="!selectedTargetWatchlist || !switchGroupReason.trim() || switchLoading"
          :loading="switchLoading"
        >
          确认切换
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { stockApi, signalApi, basicDataApi, watchlistApi } from '@/api'
import { ElMessage } from 'element-plus'
import { EditPen } from '@element-plus/icons-vue'
import StockKlineChart from '@/components/StockKlineChart.vue'
import StockAdxChart from '@/components/StockAdxChart.vue'
import StockVolumeChart from '@/components/StockVolumeChart.vue'
import StockMacdChart from '@/components/StockMacdChart.vue'

const props = defineProps(['tsCode'])

const stock = ref(null)
const klineData = ref([])
const klinePeriod = ref('daily')
const latestSignal = ref(null)
const klineChartRef = ref(null)
const adxChartRef = ref(null)
const volumeChartRef = ref(null)
const macdChartRef = ref(null)

const moneyflowLoading = ref(false)
const moneyflowData = ref([])
const showLargeOnly = ref(true)
const moneyflowChart = ref(null)
let moneyflowChartInstance = null

// 信号时间线数据
const signalsLoading = ref(false)
const signalList = ref([])

// 股票备注相关
const showNotesDialog = ref(false)
const stockNotesInput = ref('')
const notesLoading = ref(false)
const notesInputRef = ref(null)

// 所属分组相关
const watchlistStockInfo = ref(null)
const showSwitchGroupDialog = ref(false)
const selectedTargetWatchlist = ref(null)
const switchGroupReason = ref('')
const switchLoading = ref(false)
const availableWatchlists = ref([])

// Ctrl+X 按键序列状态
let ctrlXPending = false
let ctrlXTimer = null

const handleKeydown = (e) => {
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault()
    if (showNotesDialog.value && stockNotesInput.value.trim() && !notesLoading.value) {
      saveStockNotes()
    }
  }
  // Ctrl+X 前缀
  if (e.ctrlKey && e.key === 'x') {
    e.preventDefault()
    ctrlXPending = true
    clearTimeout(ctrlXTimer)
    ctrlXTimer = setTimeout(() => { ctrlXPending = false }, 2000)
    return
  }
  if (ctrlXPending && e.key === 'o') {
    e.preventDefault()
    ctrlXPending = false
    clearTimeout(ctrlXTimer)
    if (stock.value) {
      openXueqiu(stock.value)
    }
  }
  // Ctrl+X -> N: 打开备注弹窗
  if (ctrlXPending && e.key === 'n') {
    e.preventDefault()
    ctrlXPending = false
    clearTimeout(ctrlXTimer)
    if (!showNotesDialog.value) {
      openNotesDialog()
    }
  }
}

onMounted(() => {
  loadStockDetail()
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  if (moneyflowChartInstance) {
    moneyflowChartInstance.dispose()
    moneyflowChartInstance = null
  }
})

const handleResize = () => {
  klineChartRef.value?.resize()
  adxChartRef.value?.resize()
  volumeChartRef.value?.resize()
  macdChartRef.value?.resize()
  if (moneyflowChartInstance) {
    moneyflowChartInstance.resize()
  }
}

const loadStockDetail = async () => {
  try {
    const response = await stockApi.getDetail(props.tsCode)
    stock.value = response.data
    if (stock.value?.name) {
      document.title = stock.value.name
    }

    await loadKline()
    await loadSignal()
    await loadMoneyflow()
    await loadSignals()
    await loadWatchlistStockInfo()
    await fetchWatchlistOptions()
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
    dataZoom: [{ type: 'inside', start: 0, end: 100, zoomOnMouseWheel: true, moveOnMouseWheel: true }],
    series: series
  }

  moneyflowChartInstance.setOption(option, true)
}

// 资金流向汇总：5日/10日/20日净流入
const moneyflowSummary = computed(() => {
  const data = moneyflowData.value
  if (!data || data.length === 0) return null

  // 仅计算大单(20万-100万) + 特大单(>=100万)
  const calcNetInflow = (items) => {
    return items.reduce((sum, item) => {
      const net = (item.buy_lg_amount - item.sell_lg_amount)
        + (item.buy_elg_amount - item.sell_elg_amount)
      return sum + net
    }, 0)
  }

  // data 按 trade_date 排列，取末尾 N 条为最近 N 天
  const d5 = calcNetInflow(data.slice(-5))
  const d10 = calcNetInflow(data.slice(-10))
  const d20 = calcNetInflow(data.slice(-20))

  return { d5, d10, d20 }
})

const formatNetInflow = (val) => {
  if (val == null) return '-'
  const abs = Math.abs(val)
  let text
  if (abs >= 10000) text = (abs / 10000).toFixed(2) + '亿'
  else text = abs.toFixed(2) + '万'
  return (val >= 0 ? '+' : '') + text
}

watch(showLargeOnly, () => {
  if (moneyflowData.value.length > 0) {
    renderMoneyflowChart()
  }
})

const loadKline = async () => {
  try {
    const response = await stockApi.getKline(props.tsCode, klinePeriod.value, 120)
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

// 加载股票所属分组信息
const loadWatchlistStockInfo = async () => {
  try {
    const response = await watchlistApi.getStockByTsCode(props.tsCode)
    if (response.success && response.data) {
      watchlistStockInfo.value = response.data
    } else {
      watchlistStockInfo.value = null
    }
  } catch (error) {
    watchlistStockInfo.value = null
  }
}

// 获取所有分组选项
const fetchWatchlistOptions = async () => {
  try {
    const response = await watchlistApi.getAll()
    if (response.success) {
      availableWatchlists.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to fetch watchlists:', error)
  }
}

// 打开切换分组弹窗
const openSwitchGroupDialog = () => {
  selectedTargetWatchlist.value = null
  switchGroupReason.value = ''
  showSwitchGroupDialog.value = true
}

// 切换股票分组
const switchStockGroup = async () => {
  if (!watchlistStockInfo.value || !selectedTargetWatchlist.value) return
  if (!switchGroupReason.value.trim()) {
    ElMessage.warning('请填写变更理由')
    return
  }

  switchLoading.value = true
  try {
    await watchlistApi.moveStockToWatchlist(
      watchlistStockInfo.value.id,
      selectedTargetWatchlist.value,
      switchGroupReason.value.trim()
    )
    ElMessage.success('切换分组成功')
    showSwitchGroupDialog.value = false
    await loadWatchlistStockInfo()
  } catch (error) {
    console.error('Failed to switch stock group:', error)
    ElMessage.error('切换分组失败')
  } finally {
    switchLoading.value = false
  }
}

// 打开股票备注弹窗
const openNotesDialog = () => {
  stockNotesInput.value = ''
  showNotesDialog.value = true
  nextTick(() => {
    notesInputRef.value?.focus()
  })
}

// 保存股票备注
const saveStockNotes = async () => {
  if (!stock.value || !stock.value.ts_code) return

  notesLoading.value = true
  try {
    const response = await signalApi.addNote(
      stock.value.ts_code,
      stockNotesInput.value.trim()
    )
    if (response.success) {
      ElMessage.success('备注添加成功')
      showNotesDialog.value = false

      // 新增一条 NOTE 信号到列表顶部
      signalList.value.unshift({
        id: response.data?.id || Date.now(),
        ts_code: stock.value.ts_code,
        signal_type: 'NOTE',
        note_content: stockNotesInput.value.trim(),
        created_at: new Date().toISOString(),
        signal_date: new Date().toISOString()
      })
    } else {
      ElMessage.error(response.error || '备注更新失败')
    }
  } catch (error) {
    console.error('Failed to update stock notes:', error)
    ElMessage.error('备注更新失败')
  } finally {
    notesLoading.value = false
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

.watchlist-info-grid {
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.watchlist-info-grid .info-item {
  display: flex;
  justify-content: space-between;
}

.watchlist-info-grid .info-item .label {
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

.moneyflow-summary {
  display: flex;
  justify-content: space-around;
  padding: 10px 0 6px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.moneyflow-summary .summary-item {
  text-align: center;
}

.moneyflow-summary .summary-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.moneyflow-summary .summary-value {
  font-size: 15px;
  font-weight: 600;
}

.moneyflow-summary .summary-value.up {
  color: #f56c6c;
}

.moneyflow-summary .summary-value.down {
  color: #67c23a;
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

/* ADX 图例 */
.adx-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #606266;
}

/* 成交量图例 */
.volume-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #606266;
}

.volume-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.volume-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* MACD 图例 */
.macd-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #606266;
}

.macd-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.macd-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.adx-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.adx-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* 指标说明卡片 */
.indicator-guide-card .guide-feature {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 8px 10px;
  background-color: #f0f9eb;
  border-radius: 4px;
}

.indicator-guide-card .guide-section {
  margin-bottom: 10px;
}

.indicator-guide-card .guide-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}

.indicator-guide-card .guide-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}

.indicator-guide-card .guide-summary {
  font-size: 13px;
  color: #303133;
  line-height: 1.8;
}

.indicator-guide-card .summary-line {
  margin-bottom: 4px;
}

.indicator-guide-card .summary-label {
  font-weight: 600;
  color: #303133;
}
</style>
