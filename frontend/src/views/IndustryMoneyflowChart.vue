<template>
  <div class="industry-moneyflow-chart-page">
    <div class="page-header">
      <h2>资金图表</h2>
      <div class="header-actions">
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="选择行业">
          <el-select
            v-model="selectedIndustries"
            multiple
            filterable
            placeholder="搜索并选择行业"
            style="width: 480px"
            :loading="sectorsLoading"
          >
            <el-option
              v-for="sector in sectorOptions"
              :key="sector.ts_code"
              :label="`${sector.name} (${sector.ts_code})`"
              :value="sector.ts_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-tag>最近60天</el-tag>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData" :disabled="selectedIndustries.length === 0">
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 图表 -->
    <el-card v-loading="loading" class="chart-card">
      <el-empty v-if="!loading && chartData.length === 0" description="请选择行业后查询数据" />
      <div v-show="chartData.length > 0" class="charts-wrapper">
        <div
          v-for="ind in chartIndustries"
          :key="ind.ts_code"
          class="chart-item"
        >
          <div class="chart-title">{{ ind.name }}</div>
          <div :ref="el => setChartRef(el, ind.ts_code)" class="chart-container"></div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { basicDataApi } from '@/api'
import * as echarts from 'echarts'

const loading = ref(false)
const sectorsLoading = ref(false)
const selectedIndustries = ref([])
const sectorOptions = ref([])
const chartData = ref([])

// 图表实例管理：ts_code -> echarts instance
const charts = new Map()
const chartRefs = new Map()

// 颜色常量
const RED = '#f56c6c'
const GREEN = '#67c23a'

// 获取行业列表
const fetchSectors = async () => {
  sectorsLoading.value = true
  try {
    const res = await basicDataApi.getMoneyflowIndThsIndustries()
    if (res.success && res.data) {
      sectorOptions.value = res.data
        .map(s => ({ ts_code: s.ts_code, name: s.name }))
        .sort((a, b) => a.ts_code.localeCompare(b.ts_code))
    } else {
      ElMessage.error(res.error || '获取行业列表失败')
    }
  } catch (err) {
    console.error('Failed to fetch sectors:', err)
    ElMessage.error('获取行业列表失败：' + (err.message || '网络错误'))
  } finally {
    sectorsLoading.value = false
  }
}

// 获取资金流向历史数据
const fetchData = async () => {
  if (selectedIndustries.value.length === 0) {
    ElMessage.warning('请先选择至少一个行业')
    return
  }

  loading.value = true
  try {
    const res = await basicDataApi.getMoneyflowIndThsHistory(selectedIndustries.value, 60)
    if (res.success) {
      chartData.value = res.data || []
      if (chartData.value.length > 0) {
        ElMessage.success(`成功获取 ${chartData.value.length} 条数据`)
        await nextTick()
        renderCharts()
      } else {
        ElMessage.info('暂无数据')
        chartData.value = []
        disposeAllCharts()
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
      chartData.value = []
      disposeAllCharts()
    }
  } catch (err) {
    console.error('Failed to fetch moneyflow history:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    chartData.value = []
    disposeAllCharts()
  } finally {
    loading.value = false
  }
}

// 重置选择
const handleReset = () => {
  selectedIndustries.value = []
  chartData.value = []
  disposeAllCharts()
}

// 按行业分组后的数据
const chartIndustries = computed(() => {
  const industryMap = {}
  const dateSet = new Set()

  chartData.value.forEach(item => {
    const code = item.ts_code
    if (!industryMap[code]) {
      industryMap[code] = {
        name: item.industry || code,
        ts_code: code,
        dataMap: {}
      }
    }
    industryMap[code].dataMap[item.trade_date] = item.net_amount
    dateSet.add(item.trade_date)
  })

  const dates = Array.from(dateSet).sort()
  const codeToName = {}
  sectorOptions.value.forEach(s => {
    codeToName[s.ts_code] = s.name
  })

  return Object.values(industryMap).map(ind => {
    const values = dates.map(d => {
      const val = ind.dataMap[d]
      return val !== undefined ? val : null
    })
    return {
      ts_code: ind.ts_code,
      name: codeToName[ind.ts_code] || ind.name,
      dates,
      values
    }
  })
})

// 收集 DOM ref
const setChartRef = (el, ts_code) => {
  if (el) {
    chartRefs.set(ts_code, el)
  }
}

// 渲染所有图表
const renderCharts = () => {
  // 先清理旧的不再需要的图表
  const currentCodes = new Set(chartIndustries.value.map(i => i.ts_code))
  for (const [code, instance] of charts.entries()) {
    if (!currentCodes.has(code)) {
      instance.dispose()
      charts.delete(code)
    }
  }

  chartIndustries.value.forEach(ind => {
    const dom = chartRefs.get(ind.ts_code)
    if (!dom) return

    let instance = charts.get(ind.ts_code)
    if (!instance) {
      instance = echarts.init(dom)
      charts.set(ind.ts_code, instance)
    }

    const option = buildSingleChartOption(ind)
    instance.setOption(option, true)
  })
}

// 构建单个行业图表配置
const buildSingleChartOption = (ind) => {
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: true,
      formatter: (params) => {
        const p = params[0]
        if (!p || p.value === null || p.value === undefined) return ''
        const prefix = p.value > 0 ? '+' : ''
        const color = p.value >= 0 ? RED : GREEN
        return `<div style="font-weight:bold;margin-bottom:5px;">${p.axisValue}</div>
                <div>${p.marker} <span style="color:${color}">${ind.name}: ${prefix}${p.value.toFixed(2)}亿</span></div>`
      }
    },
    grid: {
      left: '12%',
      right: '5%',
      top: '10%',
      bottom: '18%',
      containLabel: false
    },
    xAxis: {
      type: 'category',
      data: ind.dates,
      axisLabel: {
        formatter: (value) => value.substring(5),
        rotate: 45,
        fontSize: 10
      },
      axisLine: { lineStyle: { color: '#999' } },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '净流入（亿）',
      nameTextStyle: { fontSize: 10 },
      axisLabel: {
        formatter: (value) => value.toFixed(0),
        fontSize: 10
      },
      splitLine: { lineStyle: { type: 'dashed' } }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        bottom: '2%',
        start: 0,
        end: 100,
        height: 16
      }
    ],
    series: [
      {
        name: ind.name,
        type: 'bar',
        data: ind.values,
        itemStyle: {
          color: (params) => {
            return params.value >= 0 ? RED : GREEN
          }
        },
        barMaxWidth: 16
      }
    ]
  }
}

// 销毁所有图表
const disposeAllCharts = () => {
  for (const instance of charts.values()) {
    instance.dispose()
  }
  charts.clear()
  chartRefs.clear()
}

// 调整大小
const resize = () => {
  for (const instance of charts.values()) {
    instance.resize()
  }
}

defineExpose({ resize })

// 监听数据变化重新渲染
watch(chartData, () => {
  if (chartData.value.length > 0) {
    nextTick(() => renderCharts())
  }
}, { deep: true })

onMounted(async () => {
  await fetchSectors()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  disposeAllCharts()
})
</script>

<style scoped>
.industry-moneyflow-chart-page {
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
  color: #303133;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.filter-card {
  margin-bottom: 20px;
}

.chart-card {
  min-height: 200px;
}

.charts-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 20px;
}

.chart-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.chart-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  margin-bottom: 10px;
  text-align: center;
}

.chart-container {
  width: 100%;
  height: 320px;
}

@media (max-width: 768px) {
  .industry-moneyflow-chart-page {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .charts-wrapper {
    grid-template-columns: 1fr;
  }

  .chart-container {
    height: 280px;
  }
}
</style>
