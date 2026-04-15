<template>
  <div ref="chartRef" class="stock-kline-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

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
  // 是否显示MACD
  showMACD: {
    type: Boolean,
    default: true
  },
  // 图表高度
  height: {
    type: String,
    default: '100%'
  },
  // 图表最小高度
  minHeight: {
    type: String,
    default: '400px'
  }
})

const chartRef = ref(null)
let chart = null

// 计算EMA
const calculateEMA = (data, period) => {
  const ema = []
  const multiplier = 2 / (period + 1)
  
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      ema.push(data[i].close)
    } else {
      ema.push(data[i].close * multiplier + ema[i - 1] * (1 - multiplier))
    }
  }
  return ema
}

// 计算MACD
const calculateMACD = (data, fast = 12, slow = 26, signal = 9) => {
  const emaFast = calculateEMA(data, fast)
  const emaSlow = calculateEMA(data, slow)
  
  // DIF = EMA12 - EMA26
  const dif = emaFast.map((v, i) => v - emaSlow[i])
  
  // DEA = EMA(DIF, 9)
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
  const volumes = data.map(item => item.volume)

  // 计算移动平均线
  const ma5 = calculateMA(data, 5)
  const ma20 = calculateMA(data, 20)
  const ma30 = calculateMA(data, 30)
  const ma60 = calculateMA(data, 60)

  // 计算MACD
  let dif = [], dea = [], macd = []
  if (props.showMACD) {
    const macdData = calculateMACD(data, 12, 26, 9)
    dif = macdData.dif
    dea = macdData.dea
    macd = macdData.macd
  }

  // 构建图例数据
  const legendData = ['日K', 'MA5', 'MA20', 'MA30', 'MA60', '成交量']
  if (props.showMACD) {
    legendData.push('DIF', 'DEA', 'MACD')
  }

  // 构建tooltip formatter
  const tooltipFormatter = (params) => {
    const dataIndex = params[0].dataIndex
    const item = data[dataIndex]
    let html = `
      <div style="font-weight:bold;margin-bottom:5px;">${item.date}</div>
      <div>开: ${item.open.toFixed(2)}</div>
      <div>收: ${item.close.toFixed(2)}</div>
      <div>高: ${item.high.toFixed(2)}</div>
      <div>低: ${item.low.toFixed(2)}</div>
      <div style="font-weight:bold;color:#409eff;">量: ${(item.volume / 10000).toFixed(2)}万</div>
      <div>涨跌: ${item.change_pct > 0 ? '+' : ''}${item.change_pct.toFixed(2)}%</div>
    `
    
    // 添加MACD信息
    if (props.showMACD && dif[dataIndex] !== undefined) {
      html += `<hr style="margin:5px 0;border:none;border-top:1px solid #eee;">`
      html += `<div style="color:#f5a623;">DIF: ${dif[dataIndex]?.toFixed(3) || '-'}</div>`
      html += `<div style="color:#5470c6;">DEA: ${dea[dataIndex]?.toFixed(3) || '-'}</div>`
      html += `<div style="color:${macd[dataIndex] >= 0 ? '#f56c6c' : '#67c23a'};">MACD: ${macd[dataIndex]?.toFixed(3) || '-'}</div>`
    }
    
    // 添加均线信息
    params.forEach(param => {
      if (param.seriesName && param.seriesName.startsWith('MA') && param.value) {
        html += `<div>${param.marker} ${param.seriesName}: ${param.value.toFixed(2)}</div>`
      }
    })
    
    return html
  }

  // 构建grid配置
  const grids = [
    {
      left: '10%',
      right: '8%',
      height: '45%',
      top: '18%'
    },
    {
      left: '10%',
      right: '8%',
      top: '66%',
      height: '12%'
    }
  ]

  const xAxes = [
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
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      min: 'dataMin',
      max: 'dataMax'
    }
  ]

  const yAxes = [
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
      axisLabel: { show: false },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false }
    }
  ]

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
      }
    },
    {
      name: 'MA5',
      type: 'line',
      data: ma5,
      smooth: true,
      lineStyle: { width: 1.5, color: '#ee6666' },
      itemStyle: { color: '#ee6666' },
      symbol: 'none'
    },
    {
      name: 'MA20',
      type: 'line',
      data: ma20,
      smooth: true,
      lineStyle: { width: 1.5, color: '#3ba272' },
      itemStyle: { color: '#3ba272' },
      symbol: 'none'
    },
    {
      name: 'MA30',
      type: 'line',
      data: ma30,
      smooth: true,
      lineStyle: { width: 1.5, color: '#5470c6' },
      itemStyle: { color: '#5470c6' },
      symbol: 'none'
    },
    {
      name: 'MA60',
      type: 'line',
      data: ma60,
      smooth: true,
      lineStyle: { width: 1.5, color: '#ea7ccc' },
      itemStyle: { color: '#ea7ccc' },
      symbol: 'none'
    },
    {
      name: '成交量',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: values.map((item, index) => ({
        value: volumes[index],
        itemStyle: {
          color: item[0] > item[1] ? '#67c23a' : '#f56c6c'
        }
      })),
      barWidth: '60%'
    }
  ]

  // 添加MACD
  if (props.showMACD) {
    grids.push({
      left: '10%',
      right: '8%',
      top: '80%',
      height: '12%'
    })

    xAxes.push({
      type: 'category',
      gridIndex: 2,
      data: dates,
      scale: true,
      boundaryGap: false,
      axisLine: { onZero: false, lineStyle: { color: '#777' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: true, formatter: function (value) { return value.substring(5) } },
      min: 'dataMin',
      max: 'dataMax'
    })

    yAxes.push({
      scale: true,
      gridIndex: 2,
      splitNumber: 2,
      axisLabel: { show: true, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: true, lineStyle: { type: 'dashed', color: '#eee' } }
    })

    series.push(
      {
        name: 'DIF',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: dif,
        smooth: true,
        lineStyle: { width: 1.5, color: '#f5a623' },
        itemStyle: { color: '#f5a623' },
        symbol: 'none'
      },
      {
        name: 'DEA',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: dea,
        smooth: true,
        lineStyle: { width: 1.5, color: '#5470c6' },
        itemStyle: { color: '#5470c6' },
        symbol: 'none'
      },
      {
        name: 'MACD',
        type: 'bar',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: macd.map((value) => ({
          value: value,
          itemStyle: {
            color: value >= 0 ? '#f56c6c' : '#67c23a'
          }
        })),
        barWidth: '50%'
      }
    )
  }

  const option = {
    title: {
      text: props.stockName || '',
      left: 'center',
      top: 5,
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    legend: {
      data: legendData,
      top: 28,
      textStyle: { fontSize: 10 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: tooltipFormatter
    },
    axisPointer: {
      link: [{ xAxisIndex: 'all' }],
      label: { backgroundColor: '#777' }
    },
    grid: grids,
    xAxis: xAxes,
    yAxis: yAxes,
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: xAxes.map((_, i) => i),
        start: 50,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        xAxisIndex: xAxes.map((_, i) => i),
        top: '97%',
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
</style>
