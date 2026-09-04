<template>
  <div class="rising-sector-page">
    <div class="page-header">
      <h2>上涨板块分析</h2>
      <div class="header-actions">
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="交易日期">
          <el-date-picker
            v-model="tradeDate"
            type="date"
            placeholder="默认最新交易日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 160px"
            clearable
            @change="fetchData"
          />
        </el-form-item>
        <el-form-item label="涨幅阈值">
          <el-select v-model="threshold" style="width: 120px" @change="fetchData">
            <el-option v-for="t in thresholdOptions" :key="t" :label="`${t}%`" :value="t" />
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
              <div class="stat-value" style="color: #409eff;">{{ chartData.length }}</div>
              <div class="stat-label">板块数</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-value" style="color: #f56c6c;">{{ totalStrongUp }}</div>
              <div class="stat-label">涨幅&ge;{{ threshold }}%个股合计</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-value" style="color: #67c23a;">{{ topSector }}</div>
              <div class="stat-label">强势板块第一</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 图表区域 -->
    <el-card v-loading="loading" class="chart-card">
      <el-empty v-if="!loading && chartData.length === 0" description="暂无数据" />
      <div v-show="chartData.length > 0" ref="chartRef" class="chart-container"></div>
    </el-card>

    <!-- 数据表格 -->
    <el-card v-if="chartData.length > 0" class="data-card">
      <el-table :data="chartData" style="width: 100%" border stripe :default-sort="{ prop: 'strong_up_stocks', order: 'descending' }">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="sector_name" label="板块名称" min-width="160" sortable>
          <template #default="{ row }">
            <router-link :to="getDetailLink(row)" class="sector-link">
              {{ row.sector_name }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="idx_type" label="板块类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="idxTypeTag(row.idx_type)">{{ row.idx_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strong_up_stocks" label="涨幅≥6%家数" min-width="110" sortable align="right">
          <template #default="{ row }">
            <span class="strong-up-num">{{ row.strong_up_stocks }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_stocks" label="板块家数" min-width="100" sortable align="right" />
        <el-table-column prop="strong_up_pct" label="占比" min-width="100" sortable align="right">
          <template #default="{ row }">
            <span :class="row.strong_up_pct >= 10 ? 'pct-hot' : ''">{{ row.strong_up_pct.toFixed(2) }}%</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { basicDataApi, sectorApi } from '@/api'
import * as echarts from '@/utils/echarts'

const loading = ref(false)
const tradeDate = ref(null)
const threshold = ref(6)
const thresholdOptions = [3, 5, 6, 7, 9, 10]
const chartData = ref([])
const chartRef = ref(null)
const sectorCodeMap = ref({})
let chartInstance = null

const totalStrongUp = computed(() => {
  return chartData.value.reduce((sum, item) => sum + item.strong_up_stocks, 0)
})

const topSector = computed(() => {
  if (chartData.value.length === 0) return '-'
  return chartData.value[0].sector_name
})

const fetchData = async () => {
  loading.value = true
  const wasDateEmpty = !tradeDate.value
  try {
    const res = await basicDataApi.getStrongUpStats({
      trade_date: tradeDate.value,
      threshold: threshold.value,
      idx_type: '行业板块',
      limit: 20
    })
    if (res.success) {
      chartData.value = res.data || []
      const meta = res.meta || {}
      if (wasDateEmpty && meta.trade_date) {
        tradeDate.value = meta.trade_date
      }
      if (meta.warning) {
        ElMessage.warning(meta.warning)
      } else if (chartData.value.length > 0) {
        const dateLabel = meta.trade_date || '最新交易日'
        ElMessage.success(`共 ${chartData.value.length} 个板块，统计日期 ${dateLabel}`)
      } else {
        ElMessage.info('暂无符合条件的板块')
      }
      if (chartData.value.length > 0) {
        await nextTick()
        renderChart()
      } else {
        disposeChart()
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
      chartData.value = []
      disposeChart()
    }
  } catch (err) {
    console.error('Failed to fetch rising sector stats:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    chartData.value = []
    disposeChart()
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, 'dark-navy')
  }

  chartInstance.setOption(buildChartOption(), true)
}

const buildChartOption = () => {
  const sectorNames = chartData.value.map(item => item.sector_name)
  const upCounts = chartData.value.map(item => item.strong_up_stocks)

  return {
    title: {
      text: `各板块涨幅≥${threshold.value}%个股数量 (${tradeDate.value || '最新交易日'})`,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#1e293b'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      extraCssText: 'z-index: 99999 !important;',
      formatter: (params) => {
        const item = chartData.value[params[0].dataIndex]
        if (!item) return ''
        return `<div style="font-weight:bold;margin-bottom:6px;">${item.sector_name} (${item.idx_type})</div>`
          + `<div style="margin:2px 0;">涨幅≥${threshold.value}%: <b style="color:#f56c6c;">${item.strong_up_stocks}</b> 家</div>`
          + `<div style="margin:2px 0;">板块总数: ${item.total_stocks} 家</div>`
          + `<div style="margin:2px 0;">占比: ${item.strong_up_pct.toFixed(2)}%</div>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '16%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sectorNames,
      axisLabel: {
        rotate: 45,
        formatter: (value) => (value.length > 6 ? value.slice(0, 6) + '…' : value),
        color: '#94a3b8'
      }
    },
    yAxis: {
      type: 'value',
      name: '个股数量',
      nameTextStyle: { color: '#94a3b8' },
      minInterval: 1,
      axisLabel: { color: '#94a3b8' },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#f0f0f0'
        }
      }
    },
    series: [
      {
        name: `涨幅≥${threshold.value}%家数`,
        type: 'bar',
        data: upCounts,
        barMaxWidth: 40,
        itemStyle: {
          color: '#f56c6c',
          borderRadius: [4, 4, 0, 0]
        },
        label: {
          show: true,
          position: 'top',
          color: '#475569',
          fontWeight: 'bold'
        }
      }
    ]
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

// 与 SectorList.vue 保持一致：板块详情使用 getAllSectors 返回的 ind_<idx> 代码
const loadSectorCodeMap = async () => {
  try {
    const res = await sectorApi.getAllSectors()
    if (res.success && Array.isArray(res.data)) {
      const map = {}
      res.data.forEach((s) => { map[s.name] = s.code })
      sectorCodeMap.value = map
    }
  } catch (err) {
    console.error('Failed to load sector codes:', err)
  }
}

const getDetailLink = (row) => {
  return {
    path: '/sector/detail',
    query: {
      code: sectorCodeMap.value[row.sector_name] || row.sector_code,
      sectorType: 'industry',
      sectorName: row.sector_name
    }
  }
}

const idxTypeTag = (type) => {
  if (type === '行业板块') return 'primary'
  return 'warning'
}

watch(chartData, () => {
  if (chartData.value.length > 0) {
    nextTick(() => renderChart())
  }
}, { deep: true })

onMounted(() => {
  fetchData()
  loadSectorCodeMap()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  disposeChart()
})
</script>

<style scoped>
.rising-sector-page {
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
  color: var(--text-primary);
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
  border-top: 1px solid var(--border-subtle);
}

.stat-card {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
  background: var(--bg-input);
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.chart-card {
  margin-bottom: 20px;
  min-height: 200px;
}

.chart-container {
  width: 100%;
  height: 520px;
}

.data-card {
  min-height: 200px;
}

.strong-up-num {
  color: var(--stock-up);
  font-weight: 600;
}

.pct-hot {
  color: var(--stock-up);
  font-weight: 600;
}

.sector-link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.sector-link:hover {
  text-decoration: underline;
  color: var(--accent-hover);
}

@media (max-width: 768px) {
  .rising-sector-page {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .chart-container {
    height: 420px;
  }
}
</style>
