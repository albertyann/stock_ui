<template>
  <el-card class="mt-20" v-loading="moneyflowLoading">
    <template #header>
      <div class="card-header">
        <span>资金流向</span>
        <div class="moneyflow-legend">
          <el-checkbox v-model="showLargeOnly" size="small">仅大单</el-checkbox>
          <span class="legend-item"><span class="dot red"></span>正向</span>
          <span class="legend-item"><span class="dot green"></span>负向</span>
        </div>
      </div>
    </template>
    <div class="moneyflow-summary" v-if="moneyflowSummary">
      <div class="summary-item">
        <span class="summary-label">20日净流入</span>
        <span class="summary-value" :class="moneyflowSummary.d20 >= 0 ? 'up' : 'down'">
          {{ formatNetInflow(moneyflowSummary.d20) }}
        </span>
      </div>
      <div class="summary-item">
        <span class="summary-label">10日净流入</span>
        <span class="summary-value" :class="moneyflowSummary.d10 >= 0 ? 'up' : 'down'">
          {{ formatNetInflow(moneyflowSummary.d10) }}
        </span>
      </div>
      <div class="summary-item">
        <span class="summary-label">5日净流入</span>
        <span class="summary-value" :class="moneyflowSummary.d5 >= 0 ? 'up' : 'down'">
          {{ formatNetInflow(moneyflowSummary.d5) }}
        </span>
      </div>
    </div>
    <div ref="chartRef" style="height: 300px;"></div>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { basicDataApi } from '@/api'
import { useECharts } from '@/composables/useECharts'

const props = defineProps({
  tsCode: {
    type: String,
    required: true
  }
})

const moneyflowLoading = ref(false)
const moneyflowData = ref([])
const showLargeOnly = ref(true)

const { chartRef, render } = useECharts()

const loadMoneyflow = async () => {
  moneyflowLoading.value = true
  try {
    const response = await basicDataApi.getMoneyflow(props.tsCode, 60)
    if (response.success) {
      moneyflowData.value = response.data || []
      if (moneyflowData.value.length > 0) {
        renderMoneyflowChart()
      }
    } else {
      ElMessage.error(response.error || '获取资金流向失败')
    }
  } catch (error) {
    console.error('Failed to load moneyflow:', error)
  } finally {
    moneyflowLoading.value = false
  }
}

const renderMoneyflowChart = () => {
  if (moneyflowData.value.length === 0) return

  const data = moneyflowData.value
  const dates = data.map(item => item.trade_date)

  const smNet = data.map(item => +(item.buy_sm_amount - item.sell_sm_amount).toFixed(2))
  const mdNet = data.map(item => +(item.buy_md_amount - item.sell_md_amount).toFixed(2))
  const lgNet = data.map(item => +(item.buy_lg_amount - item.sell_lg_amount).toFixed(2))
  const elgNet = data.map(item => +(item.buy_elg_amount - item.sell_elg_amount).toFixed(2))

  const colorPos = '#f56c6c'
  const colorNeg = '#67c23a'
  const toBarData = (arr) => arr.map(v => ({ value: v, itemStyle: { color: v >= 0 ? colorPos : colorNeg } }))

  const series = []

  if (!showLargeOnly.value) {
    series.push(
      { name: '小单(<5万)', type: 'bar', stack: 'moneyflow', data: toBarData(smNet) },
      { name: '中单(5万-20万)', type: 'bar', stack: 'moneyflow', data: toBarData(mdNet) }
    )
  }

  series.push(
    { name: '大单(20万-100万)', type: 'bar', stack: 'moneyflow', data: toBarData(lgNet) },
    { name: '特大单(>=100万)', type: 'bar', stack: 'moneyflow', data: toBarData(elgNet) }
  )

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: false,
      appendToBody: true,
      className: 'moneyflow-tooltip',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      textStyle: { color: '#1e293b' },
      formatter: (params) => {
        let html = `<div style="font-weight:bold;margin-bottom:5px">${params[0].name}</div>`
        let total = 0
        params.forEach(p => {
          const val = p.value
          total += val
          const color = val >= 0 ? '#f56c6c' : '#67c23a'
          html += `<div>${p.marker} ${p.seriesName}: <span style="color:${color};font-weight:bold">${val >= 0 ? '+' : ''}${val.toFixed(2)}万</span></div>`
        })
        const totalColor = total >= 0 ? '#f56c6c' : '#67c23a'
        html += `<div style="margin-top:5px;border-top:1px solid #e2e8f0;padding-top:5px;font-weight:bold">净流入: <span style="color:${totalColor}">${total >= 0 ? '+' : ''}${total.toFixed(2)}万</span></div>`
        return html
      }
    },
    legend: { show: false },
    grid: {
      left: '8%',
      right: '4%',
      bottom: '15%',
      top: '40px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value) => value.substring(5),
        fontSize: 9,
        rotate: 30,
        color: '#94a3b8'
      },
      axisLine: {
        lineStyle: { color: '#dcdfe6' }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => {
          if (Math.abs(value) >= 10000) return (value / 10000).toFixed(1) + '亿'
          return value + '万'
        },
        fontSize: 9,
        color: '#94a3b8'
      },
      axisLine: {
        lineStyle: { color: '#dcdfe6' }
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#f0f0f0' }
      }
    },
    dataZoom: [{ type: 'inside', start: 0, end: 100, zoomOnMouseWheel: false, moveOnMouseWheel: false }],
    series: series
  }

  render(option)
}

// 资金流向汇总：5日/10日/20日净流入
const moneyflowSummary = computed(() => {
  const data = moneyflowData.value
  if (!data || data.length === 0) return null

  // 仅计算大单(20万-100万) + 特大单(>=100万)
  const calcNetInflow = (items) => {
    return items.reduce((sum, item) => {
      const net = (item.buy_lg_amount - item.sell_lg_amount)
        + (item.buy_elg_amount - item.sell_elg_amount)
      return sum + net
    }, 0)
  }

  // data 按 trade_date 排列，取末尾 N 条为最近 N 天
  const d5 = calcNetInflow(data.slice(-5))
  const d10 = calcNetInflow(data.slice(-10))
  const d20 = calcNetInflow(data.slice(-20))

  return { d5, d10, d20 }
})

const formatNetInflow = (val) => {
  if (val == null) return '-'
  const abs = Math.abs(val)
  let text
  if (abs >= 10000) text = (abs / 10000).toFixed(2) + '亿'
  else text = abs.toFixed(2) + '万'
  return (val >= 0 ? '+' : '') + text
}

watch(showLargeOnly, () => {
  if (moneyflowData.value.length > 0) {
    renderMoneyflowChart()
  }
})

onMounted(() => {
  loadMoneyflow()
})
</script>

<style scoped>
.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.moneyflow-summary {
  display: flex;
  justify-content: space-around;
  padding: 10px 0 6px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 8px;
}

.moneyflow-summary .summary-item {
  text-align: center;
}

.moneyflow-summary .summary-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.moneyflow-summary .summary-value {
  font-size: 15px;
  font-weight: 600;
}

.moneyflow-summary .summary-value.up {
  color: var(--stock-up);
}

.moneyflow-summary .summary-value.down {
  color: var(--stock-down);
}

.moneyflow-legend {
  display: flex;
  align-items: center;
  gap: 12px;
}

.moneyflow-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.moneyflow-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.moneyflow-legend .dot.red {
  background-color: var(--stock-up);
}

.moneyflow-legend .dot.green {
  background-color: var(--stock-down);
}

/* 资金流向 tooltip 层级 */
:global(.moneyflow-tooltip) {
  z-index: 9999 !important;
}
</style>
