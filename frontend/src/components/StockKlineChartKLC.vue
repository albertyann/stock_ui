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
 *  - 买卖点标记: 用内置 simpleAnnotation overlay (圆点/三角/星/菱形 + 文字) 区分信号类型,
 *    原 ECharts 版的「空心矩形 + 实心小矩形」同心标记未 1:1 还原。
 *    若需精确还原, 可通过 registerOverlay 注册自定义 overlay (KLineChart 支持)。
 *  - MA 线颜色: 内置 MA 指标, 颜色通过 styles.lines 配置; 周期数与数组下标对应。
 *  - tooltip: KLineChart tooltip 用结构化 legend 行 (非任意 HTML), 已用 custom 回调
 *    输出 开/收/高/低/涨跌 + 信号明细; MA 数值由指标 legend 自动显示在主图顶部。
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { init, dispose, registerIndicator } from 'klinecharts'

const props = defineProps({
  tsCode: { type: String, required: true },
  stockName: { type: String, default: '' },
  klineData: { type: Array, default: () => [] },
  height: { type: String, default: '200px' },
  minHeight: { type: String, default: '200px' },
  maPeriods: { type: Array, default: () => [5, 20, 30, 60] },
  buySignals: { type: Array, default: () => [] },
  /** 指标可见性控制: { ma: { ma5, ma10, ma20, ma30, ma60, ma120 }, ema: { ema9, ema21 }, boll: boolean } */
  indicatorSettings: {
    type: Object,
    default: () => ({
      ma: { ma5: true, ma10: false, ma20: true, ma30: false, ma60: true, ma120: false },
      ema: { ema9: true, ema21: true },
      boll: false
    })
  },
  /** 可视区固定显示的 K 线根数；0 表示全部显示 */
  visibleBarCount: { type: Number, default: 0 },
  /** 评估分数: [{ date: 'YYYY-MM-DD', score: number, ... }] */
  evalScores: { type: Array, default: () => [] }
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

const maPeriods = [
  { period: 5, color: '#ee6666', settingKey: 'ma5' },
  { period: 10, color: '#fac858', settingKey: 'ma10' },
  { period: 20, color: '#3ba272', settingKey: 'ma20' },
  { period: 30, color: '#5470c6', settingKey: 'ma30' },
  { period: 60, color: '#ea7ccc', settingKey: 'ma60' },
  { period: 120, color: '#91cc75', settingKey: 'ma120' }
]

// 注册独立的 MA 指标，每个周期一个 indicator，从而可以单独控制显隐
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

const emaPeriods = [
  { period: 9, color: '#00d4aa', settingKey: 'ema9' },
  { period: 21, color: '#9a60b4', settingKey: 'ema21' }
]

// 注册独立的 EMA 指标，每个周期一个 indicator，从而可以单独控制显隐
const createEMAIndicator = (period) => ({
  name: `EMA${period}`,
  shortName: `EMA${period}`,
  calcParams: [period],
  precision: 2,
  shouldOhlc: true,
  figures: [{ key: 'ema', title: `EMA${period}: `, type: 'line' }],
  calc: (dataList, indicator) => {
    const { calcParams, figures } = indicator
    const p = calcParams[0]
    let closeSum = 0
    let emaValue = null
    return dataList.map((kLineData, i) => {
      const close = kLineData.close
      closeSum += close
      const ema = {}
      if (i >= p - 1) {
        if (i > p - 1) {
          emaValue = (2 * close + (p - 1) * emaValue) / (p + 1)
        } else {
          emaValue = closeSum / p
        }
        ema[figures[0].key] = emaValue
      }
      return ema
    })
  }
})

emaPeriods.forEach(({ period }) => registerIndicator(createEMAIndicator(period)))

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

// 用 simpleAnnotation overlay 标注评估分数 (主图顶部)
const applyEvalScoreMarkers = () => {
  if (!chart || !props.evalScores || props.evalScores.length === 0) return
  const dataList = chart.getDataList()
  const scoreColor = '#9c27b0'
  props.evalScores.forEach((entry) => {
    if (entry.score == null) return
    const ts = toTimestamp(entry.date)
    const bar = dataList.find((d) => d.timestamp === ts)
    if (!bar) return
    // Place score label at the candle high (chart margin.top 提供留白)
    const scoreText = `${entry.score.toFixed(0)}`
    chart.createOverlay({
      name: 'simpleAnnotation',
      points: [{ timestamp: bar.timestamp, value: bar.high }],
      extendData: scoreText,
      styles: {
        point: { color: scoreColor, borderColor: '#ffffff', borderSize: 1, radius: 3 },
        text: { color: scoreColor, size: 11, weight: 'bold', family: 'sans-serif', backgroundColor: 'rgba(255,255,255,0.85)', borderRadius: 2, paddingLeft: 2, paddingRight: 2, paddingTop: 0, paddingBottom: 0 }
      }
    })
  })
}

// 用 simpleAnnotation overlay 标注买卖点 (主图)
const applyMarkers = () => {
  if (!chart || !props.buySignals || props.buySignals.length === 0) return
  const dataList = chart.getDataList()
  props.buySignals.forEach((signal) => {
    const ts = toTimestamp(signal.date)
    const bar = dataList.find((d) => d.timestamp === ts)
    if (!bar) return

    // ma2560 / rsi12 组合标记 (原有逻辑保持不变)
    const hasMa = !!signal.ma2560
    const hasRsi = !!signal.rsi12
    if (hasMa || hasRsi) {
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
    }

    // ma10-proximity 标记 (紫色菱形, 略低于 bar.low 避免与 ma25/rsi 标记重叠)
    if (signal.ma10) {
      const ma10Color = '#9c27b0'
      chart.createOverlay({
        name: 'simpleAnnotation',
        points: [{ timestamp: bar.timestamp, value: bar.low * 0.985 }],
        extendData: '◆',
        styles: {
          point: { color: ma10Color, borderColor: '#ffffff', borderSize: 1, radius: 5 },
          text: { color: ma10Color, size: 12, weight: 'bold', family: 'sans-serif', backgroundColor: 'transparent' }
        }
      })
    }
  })
}

// 根据 indicatorSettings 创建/更新主图指标 (MA, EMA, BOLL)
const createIndicators = () => {
  if (!chart) return

  maPeriods.forEach(({ period, color, settingKey }) => {
    chart.createIndicator(
      {
        name: `MA${period}`,
        calcParams: [period],
        styles: {
          lines: [
            { color, size: 1.5, style: 'solid', smooth: true, dashedValue: [2, 2] }
          ]
        },
        visible: !!props.indicatorSettings.ma?.[settingKey]
      },
      true,
      { id: 'candle_pane' }
    )
  })

  emaPeriods.forEach(({ period, color, settingKey }) => {
    chart.createIndicator(
      {
        name: `EMA${period}`,
        calcParams: [period],
        styles: {
          lines: [
            { color, size: 1.5, style: 'solid', smooth: true, dashedValue: [2, 2] }
          ]
        },
        visible: !!props.indicatorSettings.ema?.[settingKey]
      },
      true,
      { id: 'candle_pane' }
    )
  })

  // BOLL 布林带，默认参数 [20, 2]
  chart.createIndicator(
    {
      name: 'BOLL',
      calcParams: [20, 2],
      styles: {
        lines: [
          { color: '#409eff', size: 1.5, style: 'solid', smooth: true, dashedValue: [2, 2] },
          { color: '#67c23a', size: 1.5, style: 'dashed', smooth: true, dashedValue: [2, 2] },
          { color: '#f56c6c', size: 1.5, style: 'dashed', smooth: true, dashedValue: [2, 2] }
        ]
      },
      visible: props.indicatorSettings.boll
    },
    true,
    { id: 'candle_pane' }
  )
}

// 切换指标可见性 (klinecharts 推荐用 overrideIndicator 做纯可见性变更)
const updateIndicatorVisibility = () => {
  if (!chart) return
  maPeriods.forEach(({ period, settingKey }) => {
    chart.overrideIndicator({
      paneId: 'candle_pane',
      name: `MA${period}`,
      visible: !!props.indicatorSettings.ma?.[settingKey]
    })
  })
  emaPeriods.forEach(({ period, settingKey }) => {
    chart.overrideIndicator({
      paneId: 'candle_pane',
      name: `EMA${period}`,
      visible: !!props.indicatorSettings.ema?.[settingKey]
    })
  })
  chart.overrideIndicator({
    paneId: 'candle_pane',
    name: 'BOLL',
    visible: !!props.indicatorSettings.boll
  })
}

// 当数据量大于可视根数时，调整 barSpace 并滚动到末尾，使视口只展示最后 N 根 K 线
// 同时保留更早的数据供 MA60 等指标计算
const fitVisibleBars = () => {
  if (!chart || !chartRef.value || props.visibleBarCount <= 0) return
  const dataList = chart.getDataList()
  if (!dataList || dataList.length <= props.visibleBarCount) return

  const chartWidth = chartRef.value.clientWidth
  if (!chartWidth) return

  const barSpace = chartWidth / props.visibleBarCount
  // 限制在合理范围，避免极端值
  const clampedBarSpace = Math.max(2, Math.min(barSpace, 50))
  chart.setBarSpace(clampedBarSpace)
  chart.scrollToTimestamp(dataList[dataList.length - 1].timestamp)
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
  applyEvalScoreMarkers()
  // 数据量超过可视根数时，仅展示最后 N 根，保证指标有足够历史计算
  fitVisibleBars()
}

const initChart = () => {
  if (!chartRef.value) return
  chart = init(chartRef.value, {
    timezone: 'Asia/Shanghai',
    styles: {
      candle: {
        type: 'candle_solid',
        // 顶部留 25% 空间供评分标注文本显示
        margin: { top: 0.25, bottom: 0.05 },
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
            // 在 tooltip 中显示评估分数
            if (props.evalScores && props.evalScores.length > 0) {
              const evalEntry = props.evalScores.find(e => {
                const eTs = toTimestamp(e.date)
                return eTs === cur.timestamp
              })
              if (evalEntry && evalEntry.score != null) {
                legends.push({
                  title: { text: '评估', color: '#9c27b0' },
                  value: `评分 ${evalEntry.score.toFixed(0)}`
                })
              }
            }

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
              if (s.ma10) {
                legends.push({
                  title: { text: 'MA10回踩', color: '#9c27b0' },
                  value: `评分${s.ma10.score.toFixed(0)} 距${s.ma10.proximity_pct.toFixed(2)}%`
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

  // 根据 indicatorSettings 创建指标 (MA, EMA)
  createIndicators()

  // 去掉 K 线右侧多余的空白间隙
  chart.setOffsetRightDistance(0)

  if (props.klineData && props.klineData.length > 0) {
    renderChart()
  }
}

const resize = () => {
  chart?.resize()
  fitVisibleBars()
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

watch(
  () => props.indicatorSettings,
  () => {
    if (chart) {
      updateIndicatorVisibility()
    }
  },
  { deep: true }
)

watch(
  () => props.evalScores,
  () => {
    if (chart) {
      chart.removeOverlay()
      applyMarkers()
      applyEvalScoreMarkers()
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
