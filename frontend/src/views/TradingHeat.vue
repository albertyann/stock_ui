<template>
  <div class="trading-heat-page">
    <div class="page-header">
      <h2>交易热度</h2>
      <div class="header-actions">
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 统计概要 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ meta.total_dates ?? '-' }}</div>
          <div class="stat-label">有数据天数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ meta.avg_stock_count ?? '-' }}</div>
          <div class="stat-label">日均筛选股票数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ maxCount ?? '-' }}</div>
          <div class="stat-label">单日最多</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ latestCount ?? '-' }}</div>
          <div class="stat-label">最近一日</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 折线图 -->
    <el-card class="chart-card">
      <div ref="chartRef" class="heat-chart"></div>
      <el-empty v-if="!loading && rawData.length === 0" description="暂无交易热度数据" />
    </el-card>

    <!-- 行业堆叠柱状图 -->
    <el-card class="chart-card">
      <div class="chart-card-header">行业分布（每日筛选股票按行业汇总，仅展示 ≥ 2 只的行业）</div>
      <div ref="stackChartRef" class="stack-chart"></div>
      <el-empty v-if="!loading && !industryData" description="暂无行业分布数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from '@/utils/echarts'
import { screeningApi } from '@/api'

const chartRef = ref(null)
let chartInstance = null
const stackChartRef = ref(null)
let stackChartInstance = null
const loading = ref(false)
const rawData = ref([])
const meta = ref({})
const industryData = ref(null)

const maxCount = computed(() => {
  if (rawData.value.length === 0) return '-'
  return Math.max(...rawData.value.map((d) => d.stock_count))
})

const latestCount = computed(() => {
  if (rawData.value.length === 0) return '-'
  return rawData.value[rawData.value.length - 1].stock_count
})

function renderChart(data) {
  if (!chartRef.value || data.length === 0) return

  // 惰性初始化 echarts 实例
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const dates = data.map((d) => d.trade_date)
  const counts = data.map((d) => d.stock_count)

  const option = {
    tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'line' },
        confine: false,
        extraCssText: 'z-index: 9999;',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        textStyle: { color: '#1e293b' },
        formatter(params) {
          if (!params || params.length === 0) return ''
          const p = params[0]
          return `<div style="font-weight:bold;margin-bottom:5px">${p.name}</div>
                  <div style="display:flex;align-items:center;gap:6px">
                    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#5470c6;"></span>
                    筛选股票数：<span style="font-weight:600;color:#409eff">${p.value}</span>
                  </div>`
        },
      },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '6%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: {
        color: '#94a3b8',
        rotate: 45,
        formatter: (v) => (v ? v.substring(5) : ''),
      },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
    },

    series: [
      {
        name: '筛选股票数',
        type: 'line',
        data: counts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2, color: '#5470c6' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(84, 112, 198, 0.35)' },
              { offset: 1, color: 'rgba(84, 112, 198, 0.02)' },
            ],
          },
        },
        itemStyle: { color: '#5470c6' },
        emphasis: { focus: 'series' },
        markLine: {
          silent: true,
          label: { show: false },
          data: [
            {
              yAxis: 10,
              label: { formatter: '阈值: 10' },
              lineStyle: { color: '#f56c6c', type: 'dashed', width: 1.5 },
            },
          ],
        },
      },
    ],
  }

  chartInstance.setOption(option, true)
  chartInstance.resize()
}

function renderStackChart(data) {
  if (!stackChartRef.value || !data) return

  if (!stackChartInstance) {
    stackChartInstance = echarts.init(stackChartRef.value)
  }

  const { dates, series } = data
  const industries = Object.keys(series)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: false,
      extraCssText: 'z-index: 9999;',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1e293b' },
      formatter(params) {
        if (!params || params.length === 0) return ''
        let html =
          `<div style="font-weight:bold;margin-bottom:6px">${params[0].name}</div>`
        let hasVisible = false
        params.forEach((p) => {
          if (p.value > 0) {
            hasVisible = true
            html += `<div style="display:flex;align-items:center;gap:6px;margin:3px 0">
              <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${p.color};"></span>
              ${p.seriesName}：<span style="font-weight:600;color:#409eff">${p.value}</span> 只
            </div>`
          }
        })
        if (!hasVisible) return ''
        return html
      },
    },
    legend: {
      type: 'scroll',
      bottom: 0,
      icon: 'roundRect',
      textStyle: { color: '#94a3b8', fontSize: 11 },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '24%',
      top: '6%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        color: '#94a3b8',
        rotate: 45,
        formatter: (v) => (v ? v.substring(5) : ''),
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
      name: '股票数',
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
    },
    series: industries.map((ind) => ({
      name: ind,
      type: 'bar',
      stack: 'total',
      data: series[ind],
      emphasis: { focus: 'series' },
    })),
  }

  stackChartInstance.setOption(option, true)
  stackChartInstance.resize()
}

function onResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
  if (stackChartInstance) {
    stackChartInstance.resize()
  }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await screeningApi.getHeat(90)
    if (res.success && res.data) {
      rawData.value = res.data
      meta.value = res.meta || {}
      industryData.value = res.industry_data || null
      if (res.data.length > 0) {
        await nextTick()
        renderChart(res.data)
        if (industryData.value) {
          renderStackChart(industryData.value)
        }
      } else {
        ElMessage.info('暂无交易热度数据')
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
      rawData.value = []
    }
  } catch (err) {
    console.error('Failed to fetch trading heat:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    rawData.value = []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchData()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (stackChartInstance) {
    stackChartInstance.dispose()
    stackChartInstance = null
  }
})
</script>

<style scoped>
.trading-heat-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 22px;
  font-weight: bold;
  color: var(--accent);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

.chart-card {
  min-height: 400px;
  position: relative;
  overflow: visible;
}

.heat-chart {
  width: 100%;
  height: 480px;
}

.stack-chart {
  width: 100%;
  height: 420px;
  overflow: visible;
}

.chart-card :deep(.el-card__body) {
  overflow: visible;
}

.chart-card-header {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-subtle);
}
</style>
