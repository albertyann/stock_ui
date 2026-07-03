<template>
  <div class="stock-simple-kline-chart" :style="{ height }">
    <div ref="chartRef" class="kline-canvas"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { init, dispose, registerIndicator } from 'klinecharts'

const props = defineProps({
  tsCode: {
    type: String,
    required: true
  },
  klineData: {
    type: Array,
    default: () => []
  },
  showVolume: {
    type: Boolean,
    default: true
  },
  height: {
    type: String,
    default: '360px'
  }
})

const chartRef = ref(null)
let chart = null

const maPeriods = [
  { period: 10, color: '#fac858' },
  { period: 20, color: '#3ba272' },
  { period: 60, color: '#ea7ccc' }
]

const createMAIndicator = (period) => ({
  name: `MA${period}`,
  shortName: `MA${period}`,
  calcParams: [period],
  precision: 2,
  shouldOhlc: true,
  figures: [{ key: 'ma', title: `MA${period}: `, type: 'line' }],
  calc: (dataList, indicator) => {
    const { calcParams, figures } = indicator
    const p = calcParams[0]
    let closeSum = 0
    return dataList.map((kLineData, i) => {
      const close = kLineData.close
      closeSum += close
      const ma = {}
      if (i >= p - 1) {
        ma[figures[0].key] = closeSum / p
        closeSum -= dataList[i - (p - 1)].close
      }
      return ma
    })
  }
})

maPeriods.forEach(({ period }) => registerIndicator(createMAIndicator(period)))

// 日期 'YYYY-MM-DD' -> 本地 0 点时间戳，避免时区偏移导致日期错位
const toTimestamp = (dateStr) => new Date(`${dateStr}T00:00:00`).getTime()

const buildBars = () => {
  return props.klineData.map((item) => ({
    timestamp: toTimestamp(item.date),
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
    volume: item.volume ?? 0,
    change_pct: item.change_pct
  }))
}

const createIndicators = () => {
  if (!chart) return

  maPeriods.forEach(({ period, color }) => {
    chart.createIndicator(
      {
        name: `MA${period}`,
        calcParams: [period],
        styles: {
          lines: [
            { color, size: 1.5, style: 'solid', smooth: true, dashedValue: [2, 2] }
          ]
        },
        visible: true
      },
      true,
      { id: 'candle_pane' }
    )
  })

  if (props.showVolume) {
    chart.createIndicator(
      {
        name: 'VOL',
        calcParams: [5],
        styles: {
          bars: [{
            upColor: '#f56c6c',
            downColor: '#67c23a',
            noChangeColor: '#888888'
          }]
        }
      },
      false,
      { height: 80 }
    )
  }
}

const renderChart = () => {
  if (!chart) return
  const bars = buildBars()
  if (bars.length === 0) return
  chart.applyNewData(bars)
  chart.setOffsetRightDistance(0)
  chart.setMaxOffsetRightDistance(0)
}

const initChart = () => {
  if (!chartRef.value) return
  chart = init(chartRef.value, {
    timezone: 'Asia/Shanghai',
    styles: {
      candle: {
        type: 'candle_solid',
        margin: { top: 0.1, bottom: 0.05 },
        // A 股红涨绿跌（KLineChart 默认国际绿涨红跌，这里翻转）
        bar: {
          upColor: '#f56c6c',
          downColor: '#67c23a',
          noChangeColor: '#888888',
          upBorderColor: '#f56c6c',
          downBorderColor: '#67c23a',
          noChangeBorderColor: '#888888',
          upWickColor: '#f56c6c',
          downWickColor: '#67c23a',
          noChangeWickColor: '#888888'
        },
        tooltip: {
          custom: (data) => {
            const cur = data.current
            const pct = cur.change_pct ?? 0
            const up = pct > 0
            const pctColor = up ? '#f56c6c' : pct < 0 ? '#67c23a' : '#888888'
            return [
              { title: '开', value: cur.open.toFixed(2) },
              { title: '收', value: { text: cur.close.toFixed(2), color: pctColor } },
              { title: '高', value: cur.high.toFixed(2) },
              { title: '低', value: cur.low.toFixed(2) },
              { title: '涨跌', value: { text: `${up ? '+' : ''}${pct.toFixed(2)}%`, color: pctColor } }
            ]
          }
        }
      },
      grid: {
        horizontal: { show: true, line: { style: 'dashed', size: 1, color: '#eeeeee', dashedValue: [2, 4] } },
        vertical: { show: false, line: { style: 'dashed', size: 1, color: '#eeeeee', dashedValue: [2, 4] } }
      },
      crosshair: {
        horizontal: {
          show: true,
          line: { show: true, style: 'dashed', size: 1, color: '#888888', dashedValue: [2, 2] },
          text: { show: true, color: '#fff', size: 10, family: 'sans-serif', weight: 'normal', backgroundColor: '#5470c6', borderSize: 0, borderRadius: 2 }
        },
        vertical: {
          show: true,
          line: { show: true, style: 'dashed', size: 1, color: '#888888', dashedValue: [2, 2] },
          text: { show: true, color: '#fff', size: 10, family: 'sans-serif', weight: 'normal', backgroundColor: '#5470c6', borderSize: 0, borderRadius: 2 }
        }
      }
    }
  })
  if (!chart) return

  createIndicators()
  chart.setOffsetRightDistance(0)
  chart.setMaxOffsetRightDistance(0)
  chart.setScrollEnabled(false)
  chart.setZoomEnabled(false)

  if (props.klineData && props.klineData.length > 0) {
    renderChart()
  }
}

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chartRef.value) {
    dispose(chartRef.value)
    chart = null
  }
})

watch(
  () => props.klineData,
  () => renderChart(),
  { deep: true }
)

defineExpose({
  resize: () => {
    chart?.resize()
  }
})
</script>

<style scoped>
.stock-simple-kline-chart {
  width: 100%;
  overflow: hidden;
}

.kline-canvas {
  width: 100%;
  height: 100%;
}
</style>
