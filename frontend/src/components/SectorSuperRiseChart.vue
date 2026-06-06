<template>
  <el-card v-loading="loading" class="sector-super-rise-card">
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <span class="card-title">超涨分布（20日）</span>
          <el-text type="info" size="small" class="header-desc">
            关注列表各板块涨幅超3.14%股票占比变化
          </el-text>
        </div>
        <div class="header-right">
          <el-checkbox v-model="showAll" size="small">
            查看全部
          </el-checkbox>
          <el-button type="primary" size="small" @click="fetchData" :loading="loading">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>
    </template>
    <div ref="chartRef" class="sector-super-rise-chart"></div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { watchlistApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

const chartRef = ref(null)
let chart = null
const loading = ref(false)
const showAll = ref(false)
let chartData = null

const fetchData = async () => {
  loading.value = true
  try {
    const res = await watchlistApi.getSuperRiseDistribution(null, 20)
    if (!res.success || !res.data) {
      ElMessage.info('暂无超涨分布数据')
      return
    }
    const { dates, sectors } = res.data
    if (!dates || dates.length === 0) {
      ElMessage.info('暂无超涨分布数据')
      return
    }
    chartData = { dates, sectors }
    renderChart()
  } catch (error) {
    console.error('Failed to fetch super rise distribution data:', error)
    ElMessage.error('加载超涨分布数据失败')
  } finally {
    loading.value = false
  }
}

/**
 * 过滤板块：默认只显示最后5天数值都大于0的板块
 */
const filterSectors = (sectors) => {
  if (showAll.value) {
    return sectors
  }

  const filtered = {}
  Object.entries(sectors).forEach(([name, values]) => {
    const lastFiveDays = values.slice(-5)
    const allPositive = lastFiveDays.every(v => v > 0)
    if (allPositive) {
      filtered[name] = values
    }
  })
  return filtered
}

// 监听 showAll 变化，重新渲染图表
watch(showAll, () => {
  if (chartData) {
    renderChart()
  }
})

/**
 * 渲染折线图
 */
const renderChart = () => {
  if (!chartRef.value || !chartData) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const { dates, sectors } = chartData
  const filteredSectors = filterSectors(sectors)
  const sectorNames = Object.keys(filteredSectors)
  if (sectorNames.length === 0) {
    chart.clear()
    return
  }

  // 预设颜色池
  const colors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
    '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ff9f7f',
    '#ffdb5c', '#67e0e3', '#37a2da', '#32c5e9', '#9fe6b8',
    '#fb7293', '#e062ae', '#e690d1', '#e7bcf3', '#9d96f5'
  ]

  const series = sectorNames.map((name, index) => ({
    name,
    type: 'line',
    data: filteredSectors[name],
    smooth: true,
    symbol: 'circle',
    symbolSize: 5,
    lineStyle: {
      width: 2
    },
    emphasis: {
      focus: 'series'
    }
  }))

  const option = {
    tooltip: {
      trigger: 'axis',
      confine: false,
      appendToBody: true,
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e4e7ed',
      borderWidth: 1,
      textStyle: {
        color: '#303133'
      },
      extraCssText: 'z-index: 9999; box-shadow: 0 4px 12px rgba(0,0,0,0.15);',
      formatter: function(params) {
        if (!params || params.length === 0) return ''
        let html = `<div style="font-weight:bold;margin-bottom:8px;font-size:14px;">${params[0].axisValue}</div>`
        // 按数值降序排列
        const sortedParams = [...params].filter(p => p.value !== undefined && p.value !== null)
          .sort((a, b) => b.value - a.value)
        sortedParams.forEach(p => {
          const color = p.color || '#999'
          html += `<div style="display:flex;justify-content:space-between;align-items:center;gap:20px;margin:3px 0;">
            <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color};margin-right:6px;"></span>${p.seriesName}</span>
            <span style="font-weight:600;">${p.value}%</span>
          </div>`
        })
        return html
      }
    },
    legend: {
      data: sectorNames,
      type: 'scroll',
      bottom: 0,
      textStyle: {
        fontSize: 11
      },
      pageIconSize: 12,
      pageTextStyle: {
        fontSize: 11
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '18%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: {
        lineStyle: { color: '#dcdfe6' }
      },
      axisLabel: {
        color: '#606266',
        formatter: function(value) {
          return value ? value.substring(5) : ''
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: {
        color: '#606266',
        formatter: '{value}%'
      },
      splitLine: {
        lineStyle: {
          color: '#ebeef5',
          type: 'dashed'
        }
      }
    },
    color: colors,
    series,
    animation: true,
    animationDuration: 500
  }

  chart.setOption(option, true)
}

const handleResize = () => {
  chart?.resize()
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.sector-super-rise-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-desc {
  font-size: 12px;
}

.sector-super-rise-chart {
  width: 100%;
  height: 420px;
}
</style>
