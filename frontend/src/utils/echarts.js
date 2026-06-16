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

export * from 'echarts/core'
export default echarts
