<template>
  <div class="incremental-industry-page">
    <div class="page-header">
      <h2>增量行业</h2>
      <div class="header-actions">
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="endDate"
            type="date"
            placeholder="选择截止日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 160px"
            clearable
            @change="fetchData"
          />
        </el-form-item>
        <el-form-item label="查询天数">
          <el-select v-model="days" style="width: 120px" @change="fetchData">
            <el-option label="10天" :value="10" />
            <el-option label="20天" :value="20" />
            <el-option label="30天" :value="30" />
          </el-select>
        </el-form-item>
        <el-form-item label="最少连续增长天数">
          <el-select v-model="minGrowthDays" style="width: 120px" @change="fetchData">
            <el-option label="3天" :value="3" />
            <el-option label="5天" :value="5" />
            <el-option label="7天" :value="7" />
            <el-option label="10天" :value="10" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData" :loading="loading">查询</el-button>
        </el-form-item>
      </el-form>

      <div class="stats-row" v-if="chartData.length > 0">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-value" style="color: #409eff;">{{ displayData.length }}/{{ chartData.length }}</div>
              <div class="stat-label">显示/符合条件的行业数</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-value" style="color: #f56c6c;">{{ topIndustry }}</div>
              <div class="stat-label">净流入第一</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-value" style="color: #67c23a;">{{ maxGrowthDays }}天</div>
              <div class="stat-label">最长连续增长</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 图表区域 -->
    <el-card v-loading="loading" class="chart-card">
      <el-empty v-if="!loading && displayData.length === 0" description="暂无数据" />
      <div v-show="displayData.length > 0" ref="chartRef" class="chart-container"></div>
    </el-card>

    <!-- 数据表格 -->
    <el-card v-if="displayData.length > 0" class="data-card">
      <el-table :data="displayData" style="width: 100%" border stripe :default-sort="{ prop: 'total_net_inflow', order: 'descending' }">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="industry" label="行业名称" min-width="140" sortable>
          <template #default="{ row }">
            <router-link :to="{ path: '/sector/detail', query: { code: row.industry_code, sectorType: 'industry', sectorName: row.industry } }" class="sector-link">
              {{ row.industry }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="total_net_inflow" label="累计净流入(亿)" min-width="140" sortable align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.total_net_inflow)">{{ formatSignedAmount(row.total_net_inflow) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="growth_days" label="连续增长天数" min-width="120" sortable align="center">
          <template #default="{ row }">
            <el-tag :type="row.growth_days >= 7 ? 'danger' : row.growth_days >= 5 ? 'warning' : 'success'">{{ row.growth_days }}天</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最新每日净流入(亿)" min-width="160" align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.daily_values[row.daily_values.length - 1])">{{ formatSignedAmount(row.daily_values[row.daily_values.length - 1]) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { basicDataApi } from '@/api'
import * as echarts from '@/utils/echarts'

const loading = ref(false)
const days = ref(20)
const minGrowthDays = ref(3)
const endDate = ref(null)
const chartData = ref([])
const dates = ref([])
const chartRef = ref(null)
let chartInstance = null

const displayData = computed(() => {
  return chartData.value.slice(0, 10)
})

const topIndustry = computed(() => {
  if (displayData.value.length === 0) return '-'
  return displayData.value[0].industry
})

const maxGrowthDays = computed(() => {
  if (displayData.value.length === 0) return 0
  return Math.max(...displayData.value.map(item => item.growth_days))
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await basicDataApi.getIncrementalIndustry(days.value, minGrowthDays.value, endDate.value)
    if (res.success) {
      dates.value = res.data?.dates || []
      chartData.value = res.data?.industries || []
      if (chartData.value.length > 0) {
        const showingCount = displayData.value.length
        const totalCount = chartData.value.length
        if (showingCount < totalCount) {
          ElMessage.success(`共 ${totalCount} 个行业，显示前 ${showingCount} 个`)
        } else {
          ElMessage.success(`成功获取 ${totalCount} 个持续净流入行业`)
        }
        await nextTick()
        renderChart()
      } else {
        ElMessage.info('暂无符合条件的行业')
        disposeChart()
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
      chartData.value = []
      dates.value = []
      disposeChart()
    }
  } catch (err) {
    console.error('Failed to fetch incremental industry:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    chartData.value = []
    dates.value = []
    disposeChart()
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option = buildChartOption()
  chartInstance.setOption(option, true)
}

const buildChartOption = () => {
  const colors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
    '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ff9f7f',
    '#ffdb5c', '#67e0e3', '#37a2da', '#32c5e9', '#9fe6b8'
  ]

  const series = displayData.value.map((item, index) => ({
    name: item.industry,
    type: 'line',
    data: item.cumulative_values,
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: {
      width: 2
    },
    itemStyle: {
      color: colors[index % colors.length]
    },
    emphasis: {
      focus: 'series'
    }
  }))

  return {
    title: {
      text: endDate.value ? `${endDate.value}之前近${days.value}个交易日持续净流入增长行业` : `近${days.value}个交易日持续净流入增长行业`,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      appendToBody: true,
      extraCssText: 'z-index: 99999 !important;',
      formatter: (params) => {
        let html = `<div style="font-weight:bold;margin-bottom:8px;">${params[0].axisValue}</div>`
        params.forEach(p => {
          const color = p.color
          // 累计值
          const cumValue = p.value >= 0 ? `+${p.value.toFixed(2)}` : p.value.toFixed(2)
          // 找到对应的 industry 数据来获取当日值
          const industryData = displayData.value.find(item => item.industry === p.seriesName)
          const dataIndex = p.dataIndex
          const dailyValue = industryData ? industryData.daily_values[dataIndex] : 0
          const dailyStr = dailyValue >= 0 ? `+${dailyValue.toFixed(2)}` : dailyValue.toFixed(2)

          html += `<div style="margin: 4px 0;">${p.marker} <span style="color:${color}">${p.seriesName}</span></div>`
          html += `<div style="margin-left: 20px; font-size: 12px; color: #666;">累计: ${cumValue}亿 | 当日: ${dailyStr}亿</div>`
        })
        return html
      }
    },
    legend: {
      type: 'scroll',
      top: 30,
      left: 'center',
      right: 40
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates.value,
      axisLabel: {
        formatter: (value) => value.substring(5),
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '累计净流入（亿）',
      axisLabel: {
        formatter: (value) => value.toFixed(0)
      },
      splitLine: {
        lineStyle: {
          type: 'dashed'
        }
      }
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
        height: 20
      }
    ],
    series
  }
}

const disposeChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

const formatSignedAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  const prefix = amount > 0 ? '+' : ''
  const yi = amount
  return prefix + yi.toFixed(2) + '亿'
}

const getAmountClass = (amount) => {
  if (amount > 0) return 'amount-up'
  if (amount < 0) return 'amount-down'
  return 'amount-flat'
}

watch(chartData, () => {
  if (chartData.value.length > 0) {
    nextTick(() => renderChart())
  }
}, { deep: true })

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  disposeChart()
})
</script>

<style scoped>
.incremental-industry-page {
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

.stats-row {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.stat-card {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
  background: #f5f7fa;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.chart-card {
  margin-bottom: 20px;
  min-height: 200px;
}

.chart-container {
  width: 100%;
  height: 500px;
}

.data-card {
  min-height: 200px;
}

.amount-up {
  color: #f56c6c;
  font-weight: 600;
}

.amount-down {
  color: #67c23a;
  font-weight: 600;
}

.amount-flat {
  color: #909399;
}

.sector-link {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.sector-link:hover {
  text-decoration: underline;
  color: #66b1ff;
}

@media (max-width: 768px) {
  .incremental-industry-page {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .chart-container {
    height: 400px;
  }
}
</style>
