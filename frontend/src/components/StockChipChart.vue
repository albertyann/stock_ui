<template>
  <div ref="chartRef" class="stock-chip-chart"></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from '@/utils/echarts'

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

// 根据数据量动态计算图表高度，确保每条至少有足够空间
const chartHeight = computed(() => {
  const count = props.chipData?.length || 0
  if (count === 0) return props.height
  // 每个价格档位至少4px，最低280px，最高600px
  const minHeight = Math.max(280, count * 4)
  return Math.min(600, minHeight) + 'px'
})

const renderChart = () => {
  if (!chart || !props.chipData || props.chipData.length === 0) return

  const data = props.chipData
  const prices = data.map(item => item.price)
  const percents = data.map(item => item.percent)

  const maxPercent = Math.max(...percents)
  const avgPercent = percents.reduce((a, b) => a + b, 0) / percents.length

  const currentPriceStr = props.currentPrice ? props.currentPrice.toFixed(2) : null

  // 找到当前价在价格列表中的索引
  let currentPriceIdx = -1
  if (currentPriceStr) {
    currentPriceIdx = prices.findIndex(p => p.toFixed(2) === currentPriceStr)
  }

  // 现价标记线数据：仅使用 yAxis 方式，兼容 category 轴
  const markLineData = []
  if (currentPriceStr && currentPriceIdx >= 0) {
    markLineData.push({ yAxis: currentPriceIdx })
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: false,
      appendToBody: true,
      className: 'chip-tooltip',
      formatter: (params) => {
        const barParam = params.find(p => p.seriesName === '筹码分布')
        if (!barParam) return ''
        const idx = barParam.dataIndex
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
      top: '5%',
      bottom: '5%',
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
        interval: Math.max(0, Math.floor(prices.length / 12))
      },
      splitLine: { show: false }
    },
    series: [
      {
        name: '筹码分布',
        type: 'bar',
        data: percents.map((pct) => ({
          value: pct,
          itemStyle: {
            color: pct >= avgPercent ? '#f56c6c' : '#909399'
          }
        })),
        barWidth: '90%',
        markLine: markLineData.length > 0 ? {
          symbol: 'none',
          label: {
            position: 'end',
            formatter: `现价 ¥${props.currentPrice.toFixed(2)}`,
            fontSize: 10,
            color: '#409eff'
          },
          lineStyle: {
            color: '#409eff',
            type: 'dashed',
            width: 1.5
          },
          data: markLineData
        } : undefined
      }
    ]
  }

  chart.setOption(option, true)
}

const initChart = async () => {
  if (!chartRef.value) return
  // 等待动态高度生效后再初始化
  await nextTick()
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
  height: v-bind('chartHeight');
}

:global(.chip-tooltip) {
  z-index: 9999 !important;
}
</style>
