<template>
  <div ref="chartRef" class="stock-volume-chart"></div>
</template>

<script setup>
import { watch } from 'vue'
import { useECharts } from '@/composables/useECharts'

const props = defineProps({
  // K线数据 (需要 date, open, close, volume 字段)
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

const { chartRef, render, resize } = useECharts()

// 渲染图表
const renderChart = () => {
  if (!props.klineData || props.klineData.length === 0) return

  const data = props.klineData
  const dates = data.map(item => item.date)

  // 成交量柱状图：涨红跌绿
  const volumeData = data.map(item => ({
    value: item.volume,
    itemStyle: {
      color: item.close >= item.open ? '#f56c6c' : '#67c23a'
    }
  }))

  // 计算5日均量
  const ma5Vol = []
  for (let i = 0; i < data.length; i++) {
    if (i < 4) {
      ma5Vol.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < 5; j++) {
        sum += data[i - j].volume
      }
      ma5Vol.push(parseFloat((sum / 5).toFixed(0)))
    }
  }

  const option = {
    tooltip: {
      trigger: 'item',
      confine: false,
      appendToBody: true,
      className: 'volume-tooltip',
      formatter: (params) => {
        try {
          const idx = params.dataIndex
          const item = data[idx]
          if (!item || !item.volume) return '成交量: -'
          const vol = item.volume
          const volStr = vol >= 100000000 ? (vol / 100000000).toFixed(2) + '亿'
            : vol >= 10000 ? (vol / 10000).toFixed(2) + '万'
            : vol.toString()
          let html = `<div style="font-weight:bold;margin-bottom:5px;">${dates[idx] || ''}</div>`
          html += `<div>成交量: <span style="font-weight:bold;">${volStr}</span></div>`
          // 计算对比前一日的成交量增幅
          if (idx > 0 && data[idx - 1]) {
            const prevVol = data[idx - 1].volume
            if (prevVol && prevVol > 0) {
              const volChangePct = ((vol - prevVol) / prevVol) * 100
              const volColor = volChangePct >= 0 ? '#f56c6c' : '#67c23a'
              html += `<div>增幅: <span style="color:${volColor};font-weight:bold;">${volChangePct > 0 ? '+' : ''}${volChangePct.toFixed(2)}%</span></div>`
            }
          }
          if (item.change_pct != null) {
            html += `<div>涨跌: <span style="color:${item.change_pct >= 0 ? '#f56c6c' : '#67c23a'};">${item.change_pct > 0 ? '+' : ''}${item.change_pct.toFixed(2)}%</span></div>`
          }
          if (ma5Vol[idx] != null) {
            const ma5Str = ma5Vol[idx] >= 100000000 ? (ma5Vol[idx] / 100000000).toFixed(2) + '亿'
              : ma5Vol[idx] >= 10000 ? (ma5Vol[idx] / 10000).toFixed(2) + '万'
              : ma5Vol[idx].toString()
            html += `<div>5日均量: ${ma5Str}</div>`
          }
          return html
        } catch (e) {
          return '成交量: -'
        }
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
      boundaryGap: true,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
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
        formatter: (value) => {
          if (Math.abs(value) >= 100000000) return (value / 100000000).toFixed(1) + '亿'
          if (Math.abs(value) >= 10000) return (value / 10000).toFixed(0) + '万'
          return value
        }
      },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } }
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100, zoomOnMouseWheel: false, moveOnMouseWheel: false }
    ],
    series: [
      {
        name: '成交量',
        type: 'bar',
        data: volumeData,
        barWidth: '60%'
      },
      {
        name: 'MA5量',
        type: 'line',
        data: ma5Vol,
        smooth: true,
        lineStyle: { width: 1.2, color: '#e6a23c' },
        itemStyle: { color: '#e6a23c' },
        symbol: 'none'
      }
    ]
  }

  render(option)
}

// 调整大小
defineExpose({ resize })

watch(() => props.klineData, () => {
  renderChart()
}, { deep: true })
</script>

<style scoped>
.stock-volume-chart {
  width: 100%;
  height: v-bind('height');
}

:global(.volume-tooltip) {
  z-index: 9999 !important;
}
</style>
