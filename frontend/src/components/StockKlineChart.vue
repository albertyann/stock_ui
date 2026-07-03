<template>
  <div ref="chartRef" class="stock-kline-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from '@/utils/echarts'

const props = defineProps({
  // 股票代码
  tsCode: {
    type: String,
    required: true
  },
  // 股票名称
  stockName: {
    type: String,
    default: ''
  },
  // K线数据
  klineData: {
    type: Array,
    default: () => []
  },
  // 图表高度
  height: {
    type: String,
    default: '200px'
  },
  // 图表最小高度
  minHeight: {
    type: String,
    default: '200px'
  },
  // 移动平均线周期数组
  maPeriods: {
    type: Array,
    default: () => [5, 20, 30, 60]
  },
  buySignals: {
    type: Array,
    default: () => []
  },
  // 是否在主图下方显示成交量副图
  showVolume: {
    type: Boolean,
    default: false
  }
})

const chartRef = ref(null)
let chart = null

// 计算移动平均线
const calculateMA = (data, period) => {
  const ma = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      ma.push(null)
      continue
    }
    let sum = 0
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close
    }
    ma.push(parseFloat((sum / period).toFixed(2)))
  }
  return ma
}

// 渲染图表
const renderChart = () => {
  if (!chart || !props.klineData || props.klineData.length === 0) return
  
  const data = props.klineData
  const dates = data.map(item => item.date)
  const values = data.map(item => [item.open, item.close, item.low, item.high])
  const hasVolume = props.showVolume && data.some(item => item.volume != null)
  const volumeData = hasVolume
    ? data.map(item => ({
        value: item.volume,
        itemStyle: {
          color: item.close >= item.open ? '#f56c6c' : '#67c23a'
        }
      }))
    : []

  // 根据 maPeriods 动态计算移动平均线
  const maMap = {}
  const maColors = {
    5: '#ee6666',
    10: '#fac858',
    20: '#3ba272',
    30: '#5470c6',
    60: '#ea7ccc',
    120: '#91cc75'
  }
  props.maPeriods.forEach(period => {
    maMap[period] = calculateMA(data, period)
  })

  // 构建图例数据
  const legendData = [...props.maPeriods.map(p => `MA${p}`)]

  // 构建tooltip formatter
  const tooltipFormatter = (params) => {
    const dataIndex = params[0].dataIndex
    const item = data[dataIndex]
    const signal = props.buySignals.find(s => s.date === item.date)
    let html = `
      <div style="font-weight:bold;margin-bottom:5px;">${item.date}</div>
      <div>开: ${item.open.toFixed(2)}</div>
      <div>收: ${item.close.toFixed(2)}</div>
      <div>高: ${item.high.toFixed(2)}</div>
      <div>低: ${item.low.toFixed(2)}</div>
      <div>涨跌: ${item.change_pct > 0 ? '+' : ''}${item.change_pct.toFixed(2)}%</div>
    `

    if (hasVolume && item.volume != null) {
      const volStr = item.volume >= 100000000
        ? (item.volume / 100000000).toFixed(2) + '亿'
        : item.volume >= 10000
          ? (item.volume / 10000).toFixed(2) + '万'
          : item.volume.toString()
      html += `<div>成交量: ${volStr}</div>`
    }
    
    params.forEach(param => {
      if (param.seriesName && param.seriesName.startsWith('MA') && param.value) {
        html += `<div>${param.marker} ${param.seriesName}: ${param.value.toFixed(2)}</div>`
      }
    })

    if (signal) {
      html += '<div style="margin-top:5px;border-top:1px solid #eee;padding-top:5px;">'
      if (signal.ma2560) {
        html += `<div style="color:#e6a23c">● MA25回踩 (评分${signal.ma2560.score.toFixed(0)}, 距MA25 ${signal.ma2560.proximity_pct.toFixed(2)}%)</div>`
      }
      if (signal.rsi12) {
        html += `<div style="color:#409eff">▲ RSI12强势 (评分${signal.rsi12.score.toFixed(0)}, RSI${signal.rsi12.rsi12.toFixed(1)})</div>`
      }
      html += '</div>'
    }
    
    return html
  }

  // 构建grid配置
  const grids = hasVolume
    ? [
        {
          left: '8%',
          right: '5%',
          top: '8%',
          bottom: '30%'
        },
        {
          left: '8%',
          right: '5%',
          top: '73%',
          bottom: '12%',
          height: '15%'
        }
      ]
    : [
        {
          left: '8%',
          right: '5%',
          top: '8%',
          bottom: '18%'
        }
      ]

  const xAxes = hasVolume
    ? [
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false, lineStyle: { color: '#777' } },
          splitLine: { show: false },
          axisLabel: {
            formatter: function (value) {
              return value.substring(5)
            }
          },
          min: 'dataMin',
          max: 'dataMax',
          axisPointer: { z: 100 }
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false, lineStyle: { color: '#777' } },
          splitLine: { show: false },
          axisLabel: { show: false },
          min: 'dataMin',
          max: 'dataMax'
        }
      ]
    : [
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false, lineStyle: { color: '#777' } },
          splitLine: { show: false },
          axisLabel: {
            formatter: function (value) {
              return value.substring(5)
            }
          },
          min: 'dataMin',
          max: 'dataMax',
          axisPointer: { z: 100 }
        }
      ]

  const yAxes = hasVolume
    ? [
        {
          scale: true,
          splitArea: {
            show: true,
            areaStyle: {
              color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
            }
          }
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
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
          splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
        }
      ]
    : [
        {
          scale: true,
          splitArea: {
            show: true,
            areaStyle: {
              color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
            }
          }
        }
      ]

  const buildBuyMarkPoints = () => {
    if (!props.buySignals || props.buySignals.length === 0) return []
    const points = []
    props.buySignals.forEach(signal => {
      const dataIndex = dates.indexOf(signal.date)
      if (dataIndex === -1) return
      const lowValue = data[dataIndex].low
      const hasMa = !!signal.ma2560
      const hasRsi = !!signal.rsi12
      if (hasMa && hasRsi) {
        points.push({
          coord: [dataIndex, lowValue], symbol: 'rect', symbolSize: 18,
          symbolOffset: [0, 14],
          itemStyle: { color: 'transparent', borderColor: '#e6a23c', borderWidth: 2.5 },
          label: { show: false }, z: 100
        })
        points.push({
          coord: [dataIndex, lowValue], symbol: 'rect', symbolSize: 10,
          symbolOffset: [0, 14],
          itemStyle: { color: '#ffffff', borderColor: '#409eff', borderWidth: 2 },
          label: { show: false }, z: 101
        })
      } else if (hasMa) {
        points.push({
          coord: [dataIndex, lowValue], symbol: 'circle', symbolSize: 12,
          symbolOffset: [0, 14],
          itemStyle: { color: '#e6a23c', borderColor: '#fff', borderWidth: 1 },
          label: { show: false }
        })
      } else if (hasRsi) {
        points.push({
          coord: [dataIndex, lowValue], symbol: 'triangle', symbolSize: 12,
          symbolOffset: [0, 14],
          itemStyle: { color: '#409eff', borderColor: '#fff', borderWidth: 1 },
          label: { show: false }
        })
      }
    })
    return points
  }

  const series = [
    {
      name: '日K',
      type: 'candlestick',
      data: values,
      itemStyle: {
        color: '#f56c6c',
        color0: '#67c23a',
        borderColor: '#f56c6c',
        borderColor0: '#67c23a'
      },
      markPoint: {
        data: buildBuyMarkPoints(),
        animation: false,
        emphasis: { disabled: true }
      }
    },
    ...props.maPeriods.map(period => ({
      name: `MA${period}`,
      type: 'line',
      data: maMap[period],
      smooth: true,
      lineStyle: { width: 1.5, color: maColors[period] || '#5470c6' },
      itemStyle: { color: maColors[period] || '#5470c6' },
      symbol: 'none'
    }))
  ]

  if (hasVolume) {
    series.push({
      name: '成交量',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: volumeData,
      barWidth: '60%'
    })
  }

  const option = {
    title: {
      text: props.stockName || '',
      left: 'center',
      top: 0,
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    legend: {
      data: legendData,
      top: 0,
      textStyle: { fontSize: 10 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      confine: false,
      appendToBody: true,
      className: 'kline-tooltip',
      formatter: tooltipFormatter
    },
    grid: grids,
    xAxis: xAxes,
    yAxis: yAxes,
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: hasVolume ? [0, 1] : [0],
        start: 50,
        end: 100,
        zoomOnMouseWheel: false,
        moveOnMouseWheel: false
      },
      {
        show: true,
        type: 'slider',
        xAxisIndex: hasVolume ? [0, 1] : [0],
        top: '92%',
        start: 50,
        end: 100,
        height: 10
      }
    ],
    series: series
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

// 暴露方法给父组件
defineExpose({
  resize
})

// 监听数据变化
watch(() => props.klineData, () => {
  if (chart) {
    renderChart()
  }
}, { deep: true })

watch(() => props.buySignals, () => {
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
.stock-kline-chart {
  width: 100%;
  height: v-bind('height');
  min-height: v-bind('minHeight');
}

/* K线 tooltip 层级 */
:global(.kline-tooltip) {
  z-index: 9999 !important;
}
</style>
