<template>
  <div ref="chartRef" class="stock-adx-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from '@/utils/echarts'

const props = defineProps({
  // K线数据 (需要 high, low, close 字段)
  klineData: {
    type: Array,
    default: () => []
  },
  // ADX 周期
  period: {
    type: Number,
    default: 14
  },
  // 图表高度
  height: {
    type: String,
    default: '150px'
  }
})

const emit = defineEmits(['hoverDate', 'mouseleave'])

const chartRef = ref(null)
let chart = null

// 计算ADX (Average Directional Index)
const calculateADX = (data, period = 14) => {
  const len = data.length
  const emptyResult = { plusDI: new Array(len).fill(null), minusDI: new Array(len).fill(null), adx: new Array(len).fill(null) }
  if (len < period * 2 + 1) return emptyResult

  const tr = []
  const plusDM = []
  const minusDM = []

  // Step 1: TR, +DM, -DM
  for (let i = 0; i < len; i++) {
    if (i === 0) {
      tr.push(data[i].high - data[i].low)
      plusDM.push(0)
      minusDM.push(0)
    } else {
      const highDiff = data[i].high - data[i - 1].high
      const lowDiff = data[i - 1].low - data[i].low

      tr.push(Math.max(
        data[i].high - data[i].low,
        Math.abs(data[i].high - data[i - 1].close),
        Math.abs(data[i].low - data[i - 1].close)
      ))

      plusDM.push(highDiff > lowDiff && highDiff > 0 ? highDiff : 0)
      minusDM.push(lowDiff > highDiff && lowDiff > 0 ? lowDiff : 0)
    }
  }

  // Step 2: Wilder smoothing
  const smoothTR = new Array(len).fill(null)
  const smoothPDM = new Array(len).fill(null)
  const smoothMDM = new Array(len).fill(null)

  let sumTR = 0, sumPDM = 0, sumMDM = 0
  for (let i = 1; i <= period; i++) {
    sumTR += tr[i]
    sumPDM += plusDM[i]
    sumMDM += minusDM[i]
  }
  smoothTR[period] = sumTR
  smoothPDM[period] = sumPDM
  smoothMDM[period] = sumMDM

  for (let i = period + 1; i < len; i++) {
    smoothTR[i] = smoothTR[i - 1] - smoothTR[i - 1] / period + tr[i]
    smoothPDM[i] = smoothPDM[i - 1] - smoothPDM[i - 1] / period + plusDM[i]
    smoothMDM[i] = smoothMDM[i - 1] - smoothMDM[i - 1] / period + minusDM[i]
  }

  // Step 3: +DI, -DI, DX
  const plusDI = new Array(len).fill(null)
  const minusDI = new Array(len).fill(null)
  const dx = new Array(len).fill(null)

  for (let i = period; i < len; i++) {
    if (!smoothTR[i] || smoothTR[i] === 0) continue
    const pdi = 100 * smoothPDM[i] / smoothTR[i]
    const mdi = 100 * smoothMDM[i] / smoothTR[i]
    plusDI[i] = parseFloat(pdi.toFixed(2))
    minusDI[i] = parseFloat(mdi.toFixed(2))
    const diSum = pdi + mdi
    if (diSum > 0) {
      dx[i] = parseFloat((100 * Math.abs(pdi - mdi) / diSum).toFixed(2))
    }
  }

  // Step 4: ADX (smoothed DX)
  const adx = new Array(len).fill(null)
  let dxSum = 0
  let dxCount = 0

  for (let i = period; i < len; i++) {
    if (dx[i] === null) continue
    if (dxCount < period) {
      dxSum += dx[i]
      dxCount++
      if (dxCount === period) {
        adx[i] = parseFloat((dxSum / period).toFixed(2))
      }
    } else {
      const prevAdx = adx[i - 1] || 0
      adx[i] = parseFloat((prevAdx * (period - 1) / period + dx[i] / period).toFixed(2))
    }
  }

  return { plusDI, minusDI, adx }
}

// 渲染图表
const renderChart = () => {
  if (!chart || !props.klineData || props.klineData.length === 0) return

  const data = props.klineData
  const dates = data.map(item => item.date)
  const { plusDI, minusDI, adx } = calculateADX(data, props.period)

  // 判断最新 ADX 趋势状态
  const lastAdx = adx.filter(v => v !== null).pop() || 0
  const lastPlusDI = plusDI.filter(v => v !== null).pop() || 0
  const lastMinusDI = minusDI.filter(v => v !== null).pop() || 0
  let trendLabel = '无趋势'
  if (lastAdx >= 25) {
    trendLabel = lastPlusDI > lastMinusDI ? '上升趋势' : '下降趋势'
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      confine: false,
      appendToBody: true,
      className: 'adx-tooltip',
      formatter: (params) => {
        const idx = params[0].dataIndex
        let html = `<div style="font-weight:bold;margin-bottom:5px;">${dates[idx]}</div>`
        html += `<div style="color:#ee6666;">+DI: ${plusDI[idx] !== null ? plusDI[idx].toFixed(2) : '-'}</div>`
        html += `<div style="color:#91cc75;">-DI: ${minusDI[idx] !== null ? minusDI[idx].toFixed(2) : '-'}</div>`
        html += `<div style="color:#5470c6;font-weight:bold;">ADX: ${adx[idx] !== null ? adx[idx].toFixed(2) : '-'}</div>`
        if (adx[idx] !== null) {
          const strength = adx[idx] >= 75 ? '极强' : adx[idx] >= 50 ? '强' : adx[idx] >= 25 ? '中等' : '弱'
          html += `<div style="color:#999;margin-top:3px;">趋势强度: ${strength}</div>`
        }
        return html
      }
    },
    legend: { show: false },
    grid: {
      left: '2%',
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
      { type: 'inside', start: 50, end: 100, zoomOnMouseWheel: false, moveOnMouseWheel: false }
    ],
    series: [
      {
        name: '+DI',
        type: 'line',
        data: plusDI,
        smooth: true,
        lineStyle: { width: 1.5, color: '#ee6666' },
        itemStyle: { color: '#ee6666' },
        symbol: 'none'
      },
      {
        name: '-DI',
        type: 'line',
        data: minusDI,
        smooth: true,
        lineStyle: { width: 1.5, color: '#91cc75' },
        itemStyle: { color: '#91cc75' },
        symbol: 'none'
      },
      {
        name: 'ADX',
        type: 'line',
        data: adx,
        smooth: true,
        lineStyle: { width: 2, color: '#5470c6' },
        itemStyle: { color: '#5470c6' },
        symbol: 'none',
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', color: '#aaa', width: 1 },
          data: [
            { yAxis: 25, label: { formatter: '趋势阈值 25', position: 'insideEndTop', fontSize: 9, color: '#999' } }
          ]
        },
        markArea: {
          silent: true,
          data: [
            [{ yAxis: 25, itemStyle: { color: 'rgba(84,112,198,0.05)' } }, { yAxis: 100 }]
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

  // 监听 axis pointer 变化（鼠标悬停时触发）
  chart.on('updateAxisPointer', (event) => {
    const xAxisInfo = event.axesInfo?.[0]
    if (xAxisInfo && xAxisInfo.value != null) {
      const data = props.klineData
      const idx = xAxisInfo.value
      if (data && idx >= 0 && idx < data.length) {
        emit('hoverDate', data[idx].date)
      }
    }
  })

  // 监听鼠标离开图表
  chart.getZr().on('globalout', () => {
    emit('mouseleave')
  })

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
.stock-adx-chart {
  width: 100%;
  height: v-bind('height');
}

:global(.adx-tooltip) {
  z-index: 9999 !important;
}
</style>
