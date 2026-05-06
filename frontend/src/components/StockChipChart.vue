<template>
  <div ref="chartRef" class="stock-chip-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  chipData: {
    type: Array,
    default: () => []
  },
  currentPrice: {
    type: Number,
    default: null
  },
  height: {
    type: String,
    default: '280px'
  }
})

const chartRef = ref(null)
let chart = null

const renderChart = () => {
  if (!chart || !props.chipData || props.chipData.length === 0) return

  const data = props.chipData
  const prices = data.map(item => item.price)
  const percents = data.map(item => item.percent)

  const maxPercent = Math.max(...percents)
  const avgPercent = percents.reduce((a, b) => a + b, 0) / percents.length

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: false,
      appendToBody: true,
      className: 'chip-tooltip',
      formatter: (params) => {
        const idx = params[0].dataIndex
        const price = prices[idx]
        const pct = percents[idx]
        let html = `<div style="font-weight:bold;margin-bottom:5px">价格: ¥${price.toFixed(2)}</div>`
        html += `<div>筹码占比: <span style="font-weight:bold;">${pct.toFixed(2)}%</span></div>`
        return html
      }
    },
    legend: { show: false },
    grid: {
      left: '12%',
      right: '8%',
      top: '8%',
      bottom: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '筹码占比(%)',
      nameLocation: 'middle',
      nameGap: 25,
      axisLabel: {
        fontSize: 10,
        formatter: (value) => value.toFixed(1)
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#eee' }
      }
    },
    yAxis: {
      type: 'category',
      data: prices.map(p => p.toFixed(2)),
      axisLabel: {
        fontSize: 9,
        interval: Math.floor(prices.length / 10)
      },
      splitLine: { show: false }
    },
    series: [
      {
        name: '筹码分布',
        type: 'bar',
        data: percents.map((pct, idx) => ({
          value: pct,
          itemStyle: {
            color: pct >= avgPercent ? '#f56c6c' : '#909399'
          }
        })),
        barWidth: '90%',
        markLine: props.currentPrice ? {
          symbol: 'none',
          label: {
            position: 'end',
            formatter: '现价 ¥{c}',
            fontSize: 10
          },
          lineStyle: {
            color: '#409eff',
            type: 'solid',
            width: 1.5
          },
          data: [
            {
              xAxis: props.currentPrice,
              label: {
                formatter: `现价 ¥${props.currentPrice.toFixed(2)}`
              }
            }
          ]
        } : undefined
      }
    ]
  }

  chart.setOption(option, true)
}

const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  if (props.chipData && props.chipData.length > 0) {
    renderChart()
  }
}

const resize = () => {
  chart?.resize()
}

defineExpose({ resize })

watch(() => props.chipData, () => {
  if (chart) {
    renderChart()
  }
}, { deep: true })

watch(() => props.currentPrice, () => {
  if (chart) {
    renderChart()
  }
})

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
.stock-chip-chart {
  width: 100%;
  height: v-bind('height');
}

:global(.chip-tooltip) {
  z-index: 9999 !important;
}
</style>
