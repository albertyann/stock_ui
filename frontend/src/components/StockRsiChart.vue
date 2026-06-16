<template>
  <div ref="chartRef" class="stock-rsi-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from '@/utils/echarts'

const props = defineProps({
  // K线数据 (需要 close 字段)
  klineData: {
    type: Array,
    default: () => []
  },
  // 图表高度
  height: {
    type: String,
    default: '150px'
  }
})

const chartRef = ref(null)
let chart = null

// RSI 周期配置
const PERIODS = [
  { value: 6,  name: 'RSI6',  color: '#f5a623' },
  { value: 12, name: 'RSI12', color: '#5470c6' },
  { value: 24, name: 'RSI24', color: '#ee6666' }
]

// 计算 RSI (Wilder's smoothing)
const calculateRSI = (data, period) => {
  const len = data.length
  const rsi = new Array(len).fill(null)
  if (len < period + 1) return rsi

  const closes = data.map(item => item.close)
  const gains = []
  const losses = []

  for (let i = 1; i < len; i++) {
    const change = closes[i] - closes[i - 1]
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? -change : 0)
  }

  // 初始 SMA
  let avgGain = 0
  let avgLoss = 0
  for (let i = 0; i < period; i++) {
    avgGain += gains[i]
    avgLoss += losses[i]
  }
  avgGain /= period
  avgLoss /= period

  if (avgLoss === 0) {
    rsi[period] = 100
  } else {
    const rs = avgGain / avgLoss
    rsi[period] = parseFloat((100 - (100 / (1 + rs))).toFixed(2))
  }

  // Wilder's smoothing
  for (let i = period + 1; i < len; i++) {
    avgGain = (avgGain * (period - 1) + gains[i - 1]) / period
    avgLoss = (avgLoss * (period - 1) + losses[i - 1]) / period

    if (avgLoss === 0) {
      rsi[i] = 100
    } else {
      const rs = avgGain / avgLoss
      rsi[i] = parseFloat((100 - (100 / (1 + rs))).toFixed(2))
    }
  }

  return rsi
}

// 渲染图表
const renderChart = () => {
  if (!chart || !props.klineData || props.klineData.length === 0) return

  const data = props.klineData
  const dates = data.map(item => item.date)

  // 同时计算 RSI(6) RSI(12) RSI(24)
  const rsiData = PERIODS.map(p => ({
    ...p,
    values: calculateRSI(data, p.value)
  }))

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      confine: false,
      appendToBody: true,
      className: 'rsi-tooltip',
      formatter: (params) => {
        const idx = params[0].dataIndex
        let html = `<div style="font-weight:bold;margin-bottom:5px;">${dates[idx]}</div>`

        PERIODS.forEach((p, i) => {
          const v = rsiData[i].values[idx]
          html += `<div style="color:${p.color};font-weight:bold;">${p.name}: ${v !== null ? v.toFixed(2) : '-'}</div>`
        })

        // 以 RSI(6) 判断状态
        const rsi6 = rsiData[0].values[idx]
        if (rsi6 !== null) {
          let status = ''
          if (rsi6 >= 80) status = '严重超买'
          else if (rsi6 >= 70) status = '超买'
          else if (rsi6 <= 20) status = '严重超卖'
          else if (rsi6 <= 30) status = '超卖'
          else if (rsi6 > 50) status = '偏强'
          else status = '偏弱'
          html += `<div style="color:#999;margin-top:3px;">状态(RSI6): ${status}</div>`
        }

        return html
      }
    },
    legend: {
      show: true,
      top: 0,
      right: 5,
      itemWidth: 14,
      itemHeight: 8,
      textStyle: { fontSize: 10 },
      selected: {
        'RSI6': true,
        'RSI12': true,
        'RSI24': false
      }
    },
    grid: {
      left: '2%',
      right: '5%',
      top: '22px',
      bottom: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#777' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        fontSize: 9,
        formatter: (value) => value.substring(5)
      }
    },
    yAxis: {
      min: 0,
      max: 100,
      splitNumber: 4,
      axisLabel: { fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100, zoomOnMouseWheel: false, moveOnMouseWheel: false }
    ],
    series: [
      ...rsiData.map(p => ({
        name: p.name,
        type: 'line',
        data: p.values,
        smooth: true,
        lineStyle: { width: 1.5, color: p.color },
        itemStyle: { color: p.color },
        symbol: 'none'
      })),
      {
        name: 'MARK',
        type: 'line',
        data: [],
        symbol: 'none',
        lineStyle: { width: 0 },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', width: 1 },
          data: [
            {
              yAxis: 70,
              lineStyle: { color: '#f56c6c' },
              label: { formatter: '70', position: 'insideEndTop', fontSize: 9, color: '#f56c6c' }
            },
            {
              yAxis: 50,
              lineStyle: { color: '#999' },
              label: { formatter: '50', position: 'insideEndTop', fontSize: 9, color: '#999' }
            },
            {
              yAxis: 30,
              lineStyle: { color: '#67c23a' },
              label: { formatter: '30', position: 'insideEndTop', fontSize: 9, color: '#67c23a' }
            }
          ]
        },
        markArea: {
          silent: true,
          data: [
            [{ yAxis: 70, itemStyle: { color: 'rgba(245,108,108,0.05)' } }, { yAxis: 100 }],
            [{ yAxis: 0, itemStyle: { color: 'rgba(103,194,58,0.05)' } }, { yAxis: 30 }]
          ]
        }
      }
    ]
  }

  chart.setOption(option, true)
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  if (props.klineData && props.klineData.length > 0) {
    renderChart()
  }
}

// 调整大小
const resize = () => {
  chart?.resize()
}

defineExpose({ resize })

watch(() => props.klineData, () => {
  if (chart) {
    renderChart()
  }
}, { deep: true })

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.stock-rsi-chart {
  width: 100%;
  height: v-bind('height');
}

:global(.rsi-tooltip) {
  z-index: 9999 !important;
}
</style>
