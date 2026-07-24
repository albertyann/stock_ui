<template>
  <div class="page-container">
    <div v-if="indexInfo" class="index-detail">
      <el-page-header
        @back="$router.back()"
        :content="`${indexInfo.name} (${indexInfo.ts_code})`"
      />

      <el-card class="index-info-card mt-20">
        <div class="index-info-grid">
          <div class="info-item">
            <span class="info-label">全称</span>
            <span class="info-value">{{ indexInfo.fullname || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">市场</span>
            <span class="info-value">{{ indexInfo.market || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">发布方</span>
            <span class="info-value">{{ indexInfo.publisher || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">指数风格</span>
            <span class="info-value">{{ indexInfo.index_type || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">指数类别</span>
            <span class="info-value">{{ indexInfo.category || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">基期</span>
            <span class="info-value">{{ indexInfo.base_date || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">基点</span>
            <span class="info-value">{{ indexInfo.base_point != null ? indexInfo.base_point : '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">加权方式</span>
            <span class="info-value">{{ indexInfo.weight_rule || '-' }}</span>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20" class="mt-20">
        <el-col :span="24">
          <el-card v-loading="klineLoading">
            <template #header>
              <div class="card-header">
                <span>日K线（{{ klineData.length }}条）</span>
              </div>
            </template>
            <StockKlineChart
              :tsCode="props.tsCode"
              :klineData="klineData"
              engine="klc"
              height="400px"
              :showVolume="true"
              :maPeriods="[5, 10, 20, 30, 60]"
              :visibleBarCount="150"
              :indicatorSettings="{ ma: { ma5: true, ma10: true, ma20: true, ma30: true, ma60: true }, ema: {}, boll: false }"
            />
          </el-card>

          <el-card class="mt-20">
            <template #header>
              <div class="card-header">
                <span>交易热度</span>
              </div>
            </template>
            <div ref="heatChartRef" class="heat-chart"></div>
            <el-empty v-if="!heatLoading && heatData.length === 0" description="暂无交易热度数据" />
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div v-else-if="loadError" class="mt-20">
      <el-result status="error" title="加载失败" :sub-title="loadError">
        <template #extra>
          <el-button type="primary" @click="loadData">重新加载</el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="mt-20" v-loading="true">
      <el-empty description="加载中..." :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { basicDataApi, screeningApi } from '@/api'
import * as echarts from '@/utils/echarts'
import StockKlineChart from '@/components/StockKlineChart.vue'

const props = defineProps(['tsCode'])

const indexInfo = ref(null)
const klineData = ref([])
const klineLoading = ref(false)
const loadError = ref('')

// 交易热度
const heatChartRef = ref(null)
let heatChartInstance = null
const heatLoading = ref(false)
const heatData = ref([])

function renderHeatChart(data) {
  if (!heatChartRef.value || data.length === 0) return

  if (!heatChartInstance) {
    heatChartInstance = echarts.init(heatChartRef.value)
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

  heatChartInstance.setOption(option, true)
  heatChartInstance.resize()
}

function onHeatResize() {
  if (heatChartInstance) {
    heatChartInstance.resize()
  }
}

async function fetchHeatData() {
  heatLoading.value = true
  try {
    const res = await screeningApi.getHeat(90)
    if (res.success && res.data) {
      heatData.value = res.data
      if (res.data.length > 0) {
        await nextTick()
        renderHeatChart(res.data)
      }
    }
  } catch (err) {
    console.error('Failed to fetch heat data:', err)
  } finally {
    heatLoading.value = false
  }
}

const loadData = async () => {
  loadError.value = ''

  // Load index basic info
  try {
    const res = await basicDataApi.getIndexBasic({ ts_code: props.tsCode })
    if (res.success && res.data && res.data.length > 0) {
      indexInfo.value = res.data[0]
    } else {
      loadError.value = '未找到该指数信息'
      return
    }
  } catch (err) {
    loadError.value = '获取指数信息失败'
    return
  }

  // Load K-line data
  klineLoading.value = true
  try {
    const res = await basicDataApi.getIndexDailyKline(props.tsCode, 210)
    if (res.success) {
      // API returns newest-first; reverse for klinecharts (expects ascending)
      klineData.value = (res.data || []).reverse()
    }
  } catch (err) {
    console.error('Failed to load index kline:', err)
  } finally {
    klineLoading.value = false
  }
}

onMounted(() => {
  if (props.tsCode) {
    loadData()
  }
  fetchHeatData()
  window.addEventListener('resize', onHeatResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onHeatResize)
  if (heatChartInstance) {
    heatChartInstance.dispose()
    heatChartInstance = null
  }
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.mt-20 {
  margin-top: 20px;
}
.index-info-card {
  margin-bottom: 0;
}
.index-info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.info-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.heat-chart {
  width: 100%;
  height: 300px;
}
</style>
