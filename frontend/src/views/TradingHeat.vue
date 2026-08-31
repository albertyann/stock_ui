<template>
  <div class="trading-heat-page">
    <div class="page-header">
      <h2>交易热度</h2>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="max-width: 260px"
          clearable
          @change="fetchData"
        />
        <el-button @click="fetchData" :loading="loading">查询</el-button>
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 按策略分组：统计概要 + 折线图 + 行业分布（每个策略独立统计，不合并） -->
    <template v-for="(s, i) in STRATEGIES" :key="s.name">
      <div class="strategy-section">
        <div class="strategy-section-title">
          <span class="chart-strategy-tag" :style="{ background: s.color }"></span>
          {{ s.label }}
        </div>

        <el-row :gutter="16" class="stats-row">
          <el-col :xs="12" :sm="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-value">{{ statsOf(i).total }}</div>
              <div class="stat-label">有数据天数</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-value">{{ statsOf(i).avg }}</div>
              <div class="stat-label">日均筛选股票数</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-value">{{ statsOf(i).max }}</div>
              <div class="stat-label">单日最多</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-value">{{ statsOf(i).latest }}</div>
              <div class="stat-label">最近一日</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 折线图 -->
        <el-card class="chart-card" v-loading="loading">
          <div class="chart-card-header">{{ s.label }} - 入选股票数趋势</div>
          <div :ref="(el) => (lineChartEls[i] = el)" class="heat-chart"></div>
          <el-empty v-if="!loading && seriesData[i].length === 0" description="暂无交易热度数据" />
        </el-card>

        <!-- 行业堆叠柱状图 -->
        <el-card class="chart-card" v-loading="loading">
          <div class="chart-card-header">行业分布 - {{ s.label }}（每日筛选股票按行业汇总，仅展示 ≥ 5 只的行业）</div>
          <div :ref="(el) => (stackChartEls[i] = el)" class="stack-chart"></div>
          <el-empty v-if="!loading && !industryData[i]" description="暂无行业分布数据" />
        </el-card>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from '@/utils/echarts'
import { screeningApi } from '@/api'

const STRATEGIES = [
  { name: 'HighScoreRsiStrong', label: 'HighScoreRsiStrong', color: '#5470c6' },
  { name: 'RsiStrong', label: 'RsiStrong', color: '#91cc75' },
]

const lineChartEls = []
const lineChartInstances = []
const stackChartEls = []
const stackChartInstances = []
const loading = ref(false)
const seriesData = ref([[], []]) // 每个策略的日度数据
const industryData = ref([null, null]) // 每个策略的行业分布
const metaList = ref([{}, {}]) // 每个策略的后端 meta

function formatDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function addDays(date, days) {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

// 默认查询最近 90 天
const today = new Date()
const dateRange = ref([formatDate(addDays(today, -90)), formatDate(today)])

// 每个策略独立统计，不跨策略合并
function statsOf(i) {
  const data = seriesData.value[i] || []
  const m = metaList.value[i] || {}
  if (data.length === 0) {
    return {
      total: m.total_dates ?? '-',
      avg: m.avg_stock_count ?? '-',
      max: '-',
      latest: '-',
    }
  }
  const counts = data.map((d) => d.stock_count)
  return {
    total: m.total_dates ?? data.length,
    avg:
      m.avg_stock_count ??
      (counts.reduce((s, v) => s + v, 0) / counts.length).toFixed(1),
    max: Math.max(...counts),
    latest: counts[counts.length - 1],
  }
}

function buildLineOption(dates, counts, color, label) {
  return {
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
                  <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color};"></span>
                  筛选股票数：<span style="font-weight:600;color:#409eff">${p.value}</span>
                </div>`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '8%',
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
      name: '股票数',
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
    },
    series: [
      {
        name: label,
        type: 'line',
        data: counts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2, color },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: color + '59' },
              { offset: 1, color: color + '05' },
            ],
          },
        },
        itemStyle: { color },
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
}

function renderLineChart(i) {
  const el = lineChartEls[i]
  const data = seriesData.value[i]
  if (!el || data.length === 0) return

  // 惰性初始化 echarts 实例
  if (!lineChartInstances[i]) {
    lineChartInstances[i] = echarts.init(el)
  }

  const dates = data.map((d) => d.trade_date)
  const counts = data.map((d) => d.stock_count)
  const { color, label } = STRATEGIES[i]

  lineChartInstances[i].setOption(buildLineOption(dates, counts, color, label), true)
  lineChartInstances[i].resize()
}

function buildStackOption(data) {
  const { dates, series } = data
  const industries = Object.keys(series)

  return {
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
        let html = `<div style="font-weight:bold;margin-bottom:6px">${params[0].name}</div>`
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
}

function renderStackChart(i) {
  const el = stackChartEls[i]
  const data = industryData.value[i]
  if (!el || !data) return

  if (!stackChartInstances[i]) {
    stackChartInstances[i] = echarts.init(el)
  }

  stackChartInstances[i].setOption(buildStackOption(data), true)
  stackChartInstances[i].resize()
}

function onResize() {
  lineChartInstances.forEach((inst) => inst && inst.resize())
  stackChartInstances.forEach((inst) => inst && inst.resize())
}

async function fetchData() {
  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value || []
    // 后端语义：days 控制下界（相对今天），end_date 限制上界
    const days =
      startDate && endDate
        ? Math.floor((new Date() - new Date(startDate)) / 86400000) + 1
        : 90

    const results = await Promise.all(
      STRATEGIES.map((s) => screeningApi.getHeat(days, endDate, s.name))
    )

    const nextData = [[], []]
    const nextIndustry = [null, null]
    const nextMeta = [{}, {}]
    let anyError = null

    results.forEach((res, i) => {
      if (res.success && res.data) {
        nextData[i] = res.data
        nextIndustry[i] = res.industry_data || null
        nextMeta[i] = res.meta || {}
      } else {
        anyError = res.error || '获取数据失败'
      }
    })

    seriesData.value = nextData
    industryData.value = nextIndustry
    metaList.value = nextMeta

    if (anyError) {
      ElMessage.error(anyError)
    }

    if (nextData[0].length === 0 && nextData[1].length === 0) {
      ElMessage.info('暂无交易热度数据')
    }

    await nextTick()
    renderLineChart(0)
    renderLineChart(1)
    renderStackChart(0)
    renderStackChart(1)
  } catch (err) {
    console.error('Failed to fetch trading heat:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    seriesData.value = [[], []]
    industryData.value = [null, null]
    metaList.value = [{}, {}]
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
  lineChartInstances.forEach((inst) => {
    if (inst) {
      inst.dispose()
    }
  })
  stackChartInstances.forEach((inst) => {
    if (inst) {
      inst.dispose()
    }
  })
  lineChartInstances.splice(0)
  stackChartInstances.splice(0)
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

.strategy-section {
  margin-bottom: 32px;
}

.strategy-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
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
  margin-bottom: 16px;
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-strategy-tag {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
</style>
