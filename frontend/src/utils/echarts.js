/**
 * ECharts 按需引入（tree-shaking）
 *
 * 全量 `import * as echarts from 'echarts'` 会把整个 ~1MB 包打进 chunk。
 * 这里只注册项目实际使用的 chart / component / renderer，体积可减少 60%+。
 *
 * 使用方式：组件中 `import * as echarts from '@/utils/echarts'`
 * API 与全量包完全一致（init / use / dispose ...）。
 *
 * 如需新增图表类型或组件，在这里的 use([...]) 中追加即可。
 */
import * as echarts from 'echarts/core'

import { LineChart, BarChart, CandlestickChart } from 'echarts/charts'

import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  DataZoomInsideComponent,
  MarkLineComponent,
  MarkAreaComponent,
  AxisPointerComponent
} from 'echarts/components'

import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  // 图表
  LineChart,
  BarChart,
  CandlestickChart,
  // 组件
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  DataZoomInsideComponent,
  MarkLineComponent,
  MarkAreaComponent,
  AxisPointerComponent,
  // 渲染器
  CanvasRenderer
])

// ============================================================
// Light professional theme — matches app design system
// Applied as base layer; per-component options override these.
// ============================================================
echarts.registerTheme('dark-navy', {
  backgroundColor: 'transparent',
  textStyle: {
    color: '#475569',
    fontFamily: "'Noto Sans SC', 'PingFang SC', sans-serif"
  },
  title: {
    textStyle: { color: '#1e293b' },
    subtextStyle: { color: '#64748b' }
  },
  legend: {
    textStyle: { color: '#475569' },
    inactiveColor: '#cbd5e1'
  },
  tooltip: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e2e8f0',
    borderWidth: 1,
    textStyle: { color: '#1e293b' },
    extraCssText: 'box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08); border-radius: 10px;',
    axisPointer: {
      lineStyle: { color: 'rgba(16, 185, 129, 0.3)' },
      crossStyle: { color: 'rgba(16, 185, 129, 0.3)' },
      label: {
        backgroundColor: '#10b981',
        color: '#ffffff'
      }
    }
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: '#dcdfe6' } },
    axisTick: { lineStyle: { color: '#dcdfe6' } },
    axisLabel: { color: '#94a3b8' },
    splitLine: { show: false },
    splitArea: { show: false }
  },
  valueAxis: {
    axisLine: { lineStyle: { color: '#dcdfe6' } },
    axisTick: { lineStyle: { color: '#dcdfe6' } },
    axisLabel: { color: '#94a3b8' },
    splitLine: { lineStyle: { color: '#f0f0f0' } },
    splitArea: { show: false }
  },
  logAxis: {
    axisLine: { lineStyle: { color: '#dcdfe6' } },
    axisLabel: { color: '#94a3b8' },
    splitLine: { lineStyle: { color: '#f0f0f0' } }
  },
  timeAxis: {
    axisLine: { lineStyle: { color: '#dcdfe6' } },
    axisLabel: { color: '#94a3b8' },
    splitLine: { lineStyle: { color: '#f0f0f0' } }
  },
  dataZoom: {
    backgroundColor: '#f8fafc',
    dataBackgroundColor: '#e2e8f0',
    fillerColor: 'rgba(16, 185, 129, 0.1)',
    handleColor: '#10b981',
    handleSize: '80%',
    textStyle: { color: '#94a3b8' }
  },
  markPoint: {
    label: { color: '#1e293b' },
    emphasis: { label: { color: '#1e293b' } }
  }
})

export * from 'echarts/core'
export default echarts
