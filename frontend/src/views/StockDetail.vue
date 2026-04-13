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
            
            <div ref="klineChart" style="height: 400px;"></div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>实时行情</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { stockApi, signalApi } from '@/api'
import { ElMessage } from 'element-plus'

const props = defineProps(['tsCode'])

const stock = ref(null)
const klineData = ref([])
const klinePeriod = ref('daily')
const latestSignal = ref(null)
const klineChart = ref(null)
let chartInstance = null

onMounted(() => {
  loadStockDetail()
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

const loadStockDetail = async () => {
  try {
    const response = await stockApi.getDetail(props.tsCode)
    stock.value = response.data
    
    await loadKline()
    await loadSignal()
  } catch (error) {
    console.error('Failed to load stock detail:', error)
    ElMessage.error('加载失败')
  }
}

const loadKline = async () => {
  try {
    const response = await stockApi.getKline(props.tsCode, klinePeriod.value, 60)
    klineData.value = response.data.data
    
    if (klineData.value.length > 0) {
      renderKlineChart()
    }
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

const renderKlineChart = () => {
  if (!klineChart.value) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(klineChart.value)
  }

  const dates = klineData.value.map(item => item.date)
  const data = klineData.value.map(item => [
    item.open,
    item.close,
    item.low,
    item.high
  ])
  const volumes = klineData.value.map(item => item.volume)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: function (params) {
        const kline = params[0]
        if (!kline) return ''
        const data = kline.data
        return `
          <div style="font-weight:bold;margin-bottom:5px">${kline.name}</div>
          <div>开盘: ¥${data[1].toFixed(2)}</div>
          <div>收盘: ¥${data[2].toFixed(2)}</div>
          <div>最低: ¥${data[4].toFixed(2)}</div>
          <div>最高: ¥${data[3].toFixed(2)}</div>
          <div>成交量: ${(volumes[kline.dataIndex] / 10000).toFixed(2)}万</div>
        `
      }
    },
    legend: {
      data: ['K线', '成交量'],
      top: 10
    },
    grid: [
      {
        left: '10%',
        right: '8%',
        height: '50%'
      },
      {
        left: '10%',
        right: '8%',
        top: '68%',
        height: '16%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false, lineStyle: { color: '#666' } },
        splitLine: { show: false },
        axisLabel: { formatter: (value) => value.slice(5), color: '#666' },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        scale: true,
        splitArea: { show: true },
        axisLine: { lineStyle: { color: '#666' } },
        axisLabel: { color: '#666' }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 30, end: 100 },
      { show: true, xAxisIndex: [0, 1], type: 'slider', top: '85%', start: 30, end: 100 }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: data,
        itemStyle: {
          color: '#ef232a',
          color0: '#14b143',
          borderColor: '#ef232a',
          borderColor0: '#14b143'
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((vol, i) => {
          return {
            value: vol,
            itemStyle: {
              color: data[i][1] >= data[i][0] ? '#ef232a' : '#14b143'
            }
          }
        })
      }
    ]
  }

  chartInstance.setOption(option, true)
}

const getChangeClass = (change) => {
  if (!change) return ''
  return change > 0 ? 'up' : change < 0 ? 'down' : ''
}

const getSignalType = (type) => {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'info' }
  return map[type] || 'info'
}

const formatSignal = (type) => {
  const map = { BUY: '买入', SELL: '卖出', WATCH: '观望' }
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
</style>
