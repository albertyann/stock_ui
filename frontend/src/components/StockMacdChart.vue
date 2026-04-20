<template>
  <div ref="chartRef" class="stock-macd-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // K线数据 (需要 close 字段)
  klineData: {
    type: Array,
    default: () => []
  },
  // 快线周期
  fast: {
    type: Number,
    default: 12
  },
  // 慢线周期
  slow: {
    type: Number,
    default: 26
  },
  // 信号线周期
  signal: {
    type: Number,
    default: 9
  },
  // 图表高度
  height: {
    type: String,
    default: '180px'
  }
})

const chartRef = ref(null)
let chart = null

// 计算EMA
const calculateEMA = (closes, period) => {
  const ema = []
  const multiplier = 2 / (period + 1)
  for (let i = 0; i < closes.length; i++) {
    if (i === 0) {
      ema.push(closes[i])
    } else {
      ema.push(closes[i] * multiplier + ema[i - 1] * (1 - multiplier))
    }
  }
  return ema
}

// 计算MACD
const calculateMACD = (data, fast = 12, slow = 26, signal = 9) => {
  const closes = data.map(item => item.close)
  const emaFast = calculateEMA(closes, fast)
  const emaSlow = calculateEMA(closes, slow)

  // DIF = EMA12 - EMA26
  const dif = emaFast.map((v, i) => v - emaSlow[i])

  // DEA = EMA(DIF, signal)
  const dea = []
  const signalMultiplier = 2 / (signal + 1)
  for (let i = 0; i < dif.length; i++) {
    if (i === 0) {
      dea.push(dif[i])
    } else {
      dea.push(dif[i] * signalMultiplier + dea[i - 1] * (1 - signalMultiplier))
    }
  }

  // MACD柱 = (DIF - DEA) * 2
  const macdBar = dif.map((v, i) => (v - dea[i]) * 2)

  return {
    dif: dif.map(v => parseFloat(v.toFixed(4))),
    dea: dea.map(v => parseFloat(v.toFixed(4))),
    macd: macdBar.map(v => parseFloat(v.toFixed(4)))
  }
}

// 渲染图表
const renderChart = () => {
  if (!chart || !props.klineData || props.klineData.length === 0) return

  const data = props.klineData
  const dates = data.map(item => item.date)
  const { dif, dea, macd } = calculateMACD(data, props.fast, props.slow, props.signal)

  // 判断最新 MACD 状态
  const lastMacd = macd.filter(v => v !== null).pop() || 0
  const lastDif = dif.filter(v => v !== null).pop() || 0
  const lastDea = dea.filter(v => v !== null).pop() || 0
  const macdStatus = lastDif > lastDea ? '多头' : '空头'
  const crossStatus = macd.length >= 2 && macd[macd.length - 1] * macd[macd.length - 2] < 0
    ? (macd[macd.length - 1] > 0 ? '金叉' : '死叉')
    : ''

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      confine: false,
      appendToBody: true,
      className: 'macd-tooltip',
      formatter: (params) => {
        const idx = params[0].dataIndex
        let html = `<div style="font-weight:bold;margin-bottom:5px;">${dates[idx]}</div>`
        html += `<div style="color:#f5a623;">DIF: ${dif[idx] !== null ? dif[idx].toFixed(3) : '-'}</div>`
        html += `<div style="color:#5470c6;">DEA: ${dea[idx] !== null ? dea[idx].toFixed(3) : '-'}</div>`
        html += `<div style="color:${macd[idx] >= 0 ? '#f56c6c' : '#67c23a'};font-weight:bold;">MACD: ${macd[idx] !== null ? macd[idx].toFixed(3) : '-'}</div>`
        if (crossStatus && idx === dates.length - 1) {
          html += `<div style="color:#e6a23c;margin-top:3px;">状态: ${crossStatus}</div>`
        }
        return html
      }
    },
    legend: { show: false },
    grid: {
      left: '10%',
      right: '5%',
      top: '8%',
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
      scale: true,
      splitNumber: 3,
      axisLabel: { fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100, zoomOnMouseWheel: true, moveOnMouseWheel: true }
    ],
    series: [
      {
        name: 'DIF',
        type: 'line',
        data: dif,
        smooth: true,
        lineStyle: { width: 1.5, color: '#f5a623' },
        itemStyle: { color: '#f5a623' },
        symbol: 'none'
      },
      {
        name: 'DEA',
        type: 'line',
        data: dea,
        smooth: true,
        lineStyle: { width: 1.5, color: '#5470c6' },
        itemStyle: { color: '#5470c6' },
        symbol: 'none'
      },
      {
        name: 'MACD',
        type: 'bar',
        data: macd.map((value) => ({
          value: value,
          itemStyle: {
            color: value >= 0 ? '#f56c6c' : '#67c23a'
          }
        })),
        barWidth: '50%'
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
.stock-macd-chart {
  width: 100%;
  height: v-bind('height');
}

:global(.macd-tooltip) {
  z-index: 9999 !important;
}
</style>
