<template>
  <div ref="chartRef" class="stock-turnover-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from '@/utils/echarts'

const props = defineProps({
  // K线数据 (需要 date, turnover_rate, change_pct 字段)
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

// 渲染图表
const renderChart = () => {
  if (!chart || !props.klineData || props.klineData.length === 0) return

  const data = props.klineData
  const dates = data.map(item => item.date)

  // 换手率折线
  const turnoverData = data.map(item => item.turnover_rate ?? null)

  // 计算5日均换手率
  const ma5Turnover = []
  for (let i = 0; i < data.length; i++) {
    if (i < 4) {
      ma5Turnover.push(null)
    } else {
      let sum = 0
      let count = 0
      for (let j = 0; j < 5; j++) {
        const v = data[i - j].turnover_rate
        if (v != null) {
          sum += v
          count++
        }
      }
      ma5Turnover.push(count > 0 ? parseFloat((sum / count).toFixed(2)) : null)
    }
  }

  // 最新换手率对应的柱状背景色（放量红，缩量绿，用于辅助识别活跃度）
  const colorPos = '#f56c6c'
  const colorNeg = '#67c23a'

  const option = {
    title: {
      text: '换手率',
      left: 'left',
      textStyle: { fontSize: 11, color: '#666', fontWeight: 'normal' },
      padding: [2, 0]
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      confine: false,
      appendToBody: true,
      className: 'turnover-tooltip',
      formatter: (params) => {
        const idx = params[0].dataIndex
        const item = data[idx]
        const tr = item.turnover_rate
        let html = `<div style="font-weight:bold;margin-bottom:5px;">${dates[idx]}</div>`
        if (tr != null) {
          html += `<div>换手率: <span style="font-weight:bold;color:${tr >= (ma5Turnover[idx] ?? 0) ? colorPos : colorNeg};">${tr.toFixed(2)}%</span></div>`
        }
        if (ma5Turnover[idx] != null) {
          html += `<div>5日均换手: ${ma5Turnover[idx].toFixed(2)}%</div>`
        }
        html += `<div>涨跌: <span style="color:${item.change_pct >= 0 ? colorPos : colorNeg};">${item.change_pct > 0 ? '+' : ''}${item.change_pct.toFixed(2)}%</span></div>`
        return html
      }
    },
    legend: { show: false },
    grid: {
      left: '2%',
      right: '5%',
      top: '15%',
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
      axisLabel: {
        fontSize: 10,
        formatter: (value) => value.toFixed(1) + '%'
      },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100, zoomOnMouseWheel: false, moveOnMouseWheel: false }
    ],
    series: [
      {
        name: '换手率',
        type: 'line',
        data: turnoverData,
        smooth: true,
        lineStyle: { width: 1.5, color: '#5470c6' },
        itemStyle: { color: '#5470c6' },
        symbol: 'none',
        areaStyle: {
          color: 'rgba(84,112,198,0.12)'
        }
      },
      {
        name: 'MA5换手',
        type: 'line',
        data: ma5Turnover,
        smooth: true,
        lineStyle: { width: 1.2, color: '#e6a23c' },
        itemStyle: { color: '#e6a23c' },
        symbol: 'none'
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
.stock-turnover-chart {
  width: 100%;
  height: v-bind('height');
  margin-top: 10px;
}

:global(.turnover-tooltip) {
  z-index: 9999 !important;
}
</style>
