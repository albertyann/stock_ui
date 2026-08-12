<template>
  <el-row :gutter="20" class="mt-20">
    <el-col :span="16">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>日线</span>
            <div class="kline-header-right">
              <span class="signal-legend" v-if="buySignalsData.length > 0">
                <span class="legend-item">
                  <span class="legend-dot" style="background-color:#e6a23c;border-radius:50%;"></span>MA25回踩
                </span>
                <span class="legend-item">
                  <span class="legend-dot legend-diamond"></span>MA10回踩
                </span>
                <span class="legend-item">
                  <span class="legend-dot legend-tri"></span>RSI12强势
                </span>
                <span class="legend-item">
                  <span class="legend-dot legend-rect"></span>双命中
                </span>
              </span>
              <div class="kline-indicator-toggles">
                <el-button size="small" link @click="$emit('open-indicator-settings')">
                  <el-icon><Setting /></el-icon>指标
                </el-button>
                <el-button
                  size="small"
                  type="success"
                  link
                  :loading="evalLoading"
                  @click="$emit('open-eval')"
                >
                  股票评估
                </el-button>
              </div>
              <el-radio-group
                :model-value="adjType"
                @update:model-value="$emit('update:adjType', $event)"
                size="small"
                class="adj-type-selector"
              >
                <el-radio-button value="forward">前复权</el-radio-button>
                <el-radio-button value="backward">后复权</el-radio-button>
                <el-radio-button value="none">不复权</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>

        <!-- 日K 使用 KLineChart 引擎，周K 使用 ECharts 引擎 -->
        <StockKlineChart
          ref="klineChartRef"
          engine="klc"
          :tsCode="tsCode"
          :klineData="adjustedKlineData"
          :buySignals="buySignalsData"
          :indicatorSettings="klineIndicatorSettings"
          :visibleBarCount="KLINE_DISPLAY_DAYS"
          :evalScores="evalScores"
          :showVolume="true"
          height="360px"
        />
      </el-card>

      <!-- 指标 -->
      <el-card class="mt-20">
        <template #header>
          <div class="card-header">
            <span>指标</span>
          </div>
        </template>
        <StockRsiChart
          ref="rsiChartRef"
          :klineData="indicatorKlineData"
        />
        <StockTurnoverChart
          ref="turnoverChartRef"
          :klineData="indicatorKlineData"
        />
        <StockVolumeChart
          ref="volumeChartRef"
          :klineData="indicatorKlineData"
        />
        <StockMacdChart
          ref="macdChartRef"
          :klineData="indicatorKlineData"
        />
        <StockAdxChart
          ref="adxChartRef"
          :klineData="indicatorKlineData"
        />

      </el-card>

      <slot name="daily-append" />
    </el-col>

    <el-col :span="8">
      <!-- 周线K线图 -->
      <el-card class="weekly-kline-card">
        <template #header>
          <div class="card-header">
            <span>周线</span>
          </div>
        </template>
        <StockKlineChart
          ref="weeklyKlineChartRef"
          :tsCode="tsCode"
          :klineData="adjustedWeeklyKlineData"
          height="360px"
          :maPeriods="[5, 10]"
          :showVolume="true"
        />
      </el-card>

      <slot name="weekly-append" />
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Setting } from '@element-plus/icons-vue'
import StockKlineChart from '@/components/StockKlineChart.vue'
import StockAdxChart from '@/components/StockAdxChart.vue'
import StockTurnoverChart from '@/components/StockTurnoverChart.vue'
import StockRsiChart from '@/components/StockRsiChart.vue'
import StockVolumeChart from '@/components/StockVolumeChart.vue'
import StockMacdChart from '@/components/StockMacdChart.vue'
import { KLINE_DISPLAY_DAYS } from '@/composables/useKlineAdjust'

defineProps({
  tsCode: {
    type: String,
    required: true
  },
  // 复权方式: forward=前复权, backward=后复权, none=不复权
  adjType: {
    type: String,
    default: 'forward'
  },
  buySignalsData: {
    type: Array,
    default: () => []
  },
  adjustedKlineData: {
    type: Array,
    default: () => []
  },
  indicatorKlineData: {
    type: Array,
    default: () => []
  },
  adjustedWeeklyKlineData: {
    type: Array,
    default: () => []
  },
  klineIndicatorSettings: {
    type: Object,
    required: true
  },
  evalLoading: {
    type: Boolean,
    default: false
  },
  // K线图上仅显示评分 > 85 的高分日期
  evalScores: {
    type: Array,
    default: () => []
  }
})

defineEmits(['update:adjType', 'open-indicator-settings', 'open-eval'])

const klineChartRef = ref(null)
const weeklyKlineChartRef = ref(null)
const adxChartRef = ref(null)
const macdChartRef = ref(null)
const rsiChartRef = ref(null)
const turnoverChartRef = ref(null)
const volumeChartRef = ref(null)

const handleResize = () => {
  klineChartRef.value?.resize()
  weeklyKlineChartRef.value?.resize()
  adxChartRef.value?.resize()
  macdChartRef.value?.resize()
  rsiChartRef.value?.resize()
  turnoverChartRef.value?.resize()
  volumeChartRef.value?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.mt-20 {
  margin-top: 20px;
}

.weekly-kline-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.adj-type-selector :deep(.el-radio-button__inner) {
  padding: 4px 10px;
  font-size: 12px;
}

.kline-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.kline-indicator-toggles {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.kline-indicator-toggles :deep(.el-checkbox__label) {
  font-size: 12px;
}

.signal-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.signal-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.signal-legend .legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.signal-legend .legend-tri {
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-bottom: 8px solid var(--accent);
}

.signal-legend .legend-diamond {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: var(--accent-cyan);
  transform: rotate(45deg);
}

.signal-legend .legend-rect {
  display: inline-block;
  width: 10px;
  height: 10px;
  background: var(--bg-card-solid);
  border: 2px solid var(--warning);
  box-shadow: inset 0 0 0 1.5px var(--accent);
}
</style>
