<template>
  <div class="stock-kline-chart-klc" :style="{ height, minHeight }">
    <div v-if="stockName" class="klc-title">{{ stockName }}</div>
    <div ref="chartRef" class="klc-canvas"></div>
  </div>
</template>

<script setup>
/**
 * POC: KLineChart (v9) 版本的日 K 图，props 与 StockKlineChart.vue 完全兼容。
 *
 * 与 ECharts 版的差异 / 已知限制（POC LIMITATION）:
 *  - 买卖点标记: 用内置 simpleAnnotation overlay (圆点 + 文字) 区分信号类型,
 *    原 ECharts 版的「空心矩形 + 实心小矩形」同心标记未 1:1 还原。
 *    若需精确还原, 可通过 registerOverlay 注册自定义 overlay (KLineChart 支持)。
 *  - MA 线颜色: 内置 MA 指标, 颜色通过 styles.lines 配置; 周期数与数组下标对应。
 *  - tooltip: KLineChart tooltip 用结构化 legend 行 (非任意 HTML), 已用 custom 回调
 *    输出 开/收/高/低/涨跌 + 信号明细; MA 数值由指标 legend 自动显示在主图顶部。
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { init, dispose } from 'klinecharts'

const props = defineProps({
  tsCode: { type: String, required: true },
  stockName: { type: String, default: '' },
  klineData: { type: Array, default: () => [] },
  height: { type: String, default: '200px' },
  minHeight: { type: String, default: '200px' },
  maPeriods: { type: Array, default: () => [5, 20, 30, 60] },
  buySignals: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chart = null

const maColors = {
  5: '#ee6666',
  10: '#fac858',
  20: '#3ba272',
  30: '#5470c6',
  60: '#ea7ccc',
  120: '#91cc75'
}

// 日期 'YYYY-MM-DD' -> 本地 0 点时间戳, 避免时区偏移导致日期错位
const toTimestamp = (dateStr) => new Date(`${dateStr}T00:00:00`).getTime()

// 把业务数据映射成 KLineChart 所需格式, 并把 change_pct / 信号挂到 bar 上供 tooltip 读取
const buildBars = () => {
  const signalMap = {}
  props.buySignals.forEach((s) => {
    signalMap[s.date] = s
  })
  return props.klineData.map((item) => ({
    timestamp: toTimestamp(item.date),
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
    // 额外字段 (KLineData 允许任意 key), tooltip 回调里取用
    change_pct: item.change_pct,
    signal: signalMap[item.date] || null
  }))
}

// 用 simpleAnnotation overlay 标注买卖点 (主图)
const applyMarkers = () => {
  if (!chart || !props.buySignals || props.buySignals.length === 0) return
  const dataList = chart.getDataList()
  props.buySignals.forEach((signal) => {
    const ts = toTimestamp(signal.date)
    const bar = dataList.find((d) => d.timestamp === ts)
    if (!bar) return

    const hasMa = !!signal.ma2560
    const hasRsi = !!signal.rsi12
    // 用文字 + 颜色区分信号类型
    let text = '●'
    let color = '#e6a23c'
    if (hasMa && hasRsi) {
      text = '★'
      color = '#e6a23c'
    } else if (hasRsi) {
      text = '▲'
      color = '#409eff'
    }
    chart.createOverlay({
      name: 'simpleAnnotation',
      points: [{ timestamp: bar.timestamp, value: bar.low }],
      extendData: text,
      styles: {
        point: { color, borderColor: '#ffffff', borderSize: 1, radius: 5 },
        text: { color, size: 12, weight: 'bold', family: 'sans-serif', backgroundColor: 'transparent' }
      }
    })
  })
}

const renderChart = () => {
  if (!chart) return
  const bars = buildBars()
  if (bars.length === 0) return
  chart.applyNewData(bars)
  // 让 K 线占满右侧区域, 不留空白
  chart.setOffsetRightDistance(0)
  chart.setMaxOffsetRightDistance(0)
  // 覆盖物在 applyNewData 后保留, 先清再加, 避免重复
  chart.removeOverlay()
  applyMarkers()
}

const initChart = () => {
  if (!chartRef.value) return
  chart = init(chartRef.value, {
    timezone: 'Asia/Shanghai',
    styles: {
      candle: {
        type: 'candle_solid',
        // A 股红涨绿跌 (KLineChart 默认是国际绿涨红跌, 这里翻转)
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
          // 用结构化 legend 行自定义 tooltip, 输出 OHLC + 涨跌 + 信号明细
          custom: (data) => {
            const cur = data.current
            const pct = cur.change_pct
            const up = pct > 0
            const pctColor = up ? '#f56c6c' : pct < 0 ? '#67c23a' : '#888888'
            const legends = [
              { title: '开', value: cur.open.toFixed(2) },
              { title: '收', value: { text: cur.close.toFixed(2), color: pctColor } },
              { title: '高', value: cur.high.toFixed(2) },
              { title: '低', value: cur.low.toFixed(2) },
              { title: '涨跌', value: { text: `${up ? '+' : ''}${pct.toFixed(2)}%`, color: pctColor } }
            ]
            const s = cur.signal
            if (s) {
              if (s.ma2560) {
                legends.push({
                  title: { text: 'MA25回踩', color: '#e6a23c' },
                  value: `评分${s.ma2560.score.toFixed(0)} 距${s.ma2560.proximity_pct.toFixed(2)}%`
                })
              }
              if (s.rsi12) {
                legends.push({
                  title: { text: 'RSI12强势', color: '#409eff' },
                  value: `评分${s.rsi12.score.toFixed(0)} RSI${s.rsi12.rsi12.toFixed(1)}`
                })
              }
            }
            return legends
          }
        }
      },
      // 让默认字体/颜色偏暗, 贴合现有深色背景观感
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

  // MA 指标叠加在主图 (isStack=true), 周期与颜色按 props 配置
  const lines = props.maPeriods.map((p) => ({
    color: maColors[p] || '#5470c6',
    size: 1.5,
    style: 'solid',
    smooth: true,
    dashedValue: [2, 2]
  }))
  chart.createIndicator(
    { name: 'MA', calcParams: props.maPeriods, styles: { lines } },
    true,
    { id: 'candle_pane' }
  )

  // 去掉 K 线右侧多余的空白间隙
  chart.setOffsetRightDistance(0)

  if (props.klineData && props.klineData.length > 0) {
    renderChart()
  }
}

const resize = () => {
  chart?.resize()
}

defineExpose({ resize })

watch(
  () => props.klineData,
  () => renderChart(),
  { deep: true }
)

watch(
  () => props.buySignals,
  () => {
    if (chart) {
      chart.removeOverlay()
      applyMarkers()
    }
  },
  { deep: true }
)

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chartRef.value) {
    dispose(chartRef.value)
    chart = null
  }
})
</script>

<style scoped>
.stock-kline-chart-klc {
  position: relative;
  width: 100%;
}

.klc-title {
  position: absolute;
  top: 2px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 14px;
  font-weight: normal;
  z-index: 2;
  pointer-events: none;
}

.klc-canvas {
  width: 100%;
  height: 100%;
}
</style>
