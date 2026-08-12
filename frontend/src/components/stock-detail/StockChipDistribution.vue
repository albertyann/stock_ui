<template>
  <!-- 筹码分布 -->
  <el-card class="mt-20" v-loading="chipLoading">
    <template #header>
      <div class="card-header">
        <span>筹码分布</span>
        <el-date-picker
          v-model="selectedChipDate"
          type="date"
          placeholder="选择日期"
          size="small"
          style="width: 140px"
          value-format="YYYY-MM-DD"
          @change="onChipDateChange"
        />
      </div>
    </template>
    <div v-if="chipData.chips && chipData.chips.length > 0">
      <div class="chip-summary" v-if="chipConcentration !== null">
        <div class="summary-item">
          <span class="summary-label">筹码集中度</span>
          <span class="summary-value">{{ chipConcentration.toFixed(2) }}%</span>
        </div>
      </div>
      <StockChipChart
        ref="chipChartRef"
        :chipData="chipData.chips"
        :currentPrice="chipData.current_price"
        height="280px"
      />
    </div>
    <el-empty v-else description="暂无筹码数据" :image-size="60" />
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { basicDataApi } from '@/api'
import StockChipChart from '@/components/StockChipChart.vue'

const props = defineProps({
  tsCode: {
    type: String,
    required: true
  }
})

const chipLoading = ref(false)
const chipData = ref({ chips: [], current_price: null, trade_date: null })
const chipChartRef = ref(null)
const selectedChipDate = ref(null)

const loadCyqChips = async (date = null) => {
  chipLoading.value = true
  try {
    const response = await basicDataApi.getCyqChips(props.tsCode, date)
    if (response.success && response.data) {
      chipData.value = {
        chips: response.data.chips || [],
        current_price: response.data.current_price || null,
        trade_date: response.data.trade_date || null
      }
    }
  } catch (error) {
    console.error('Failed to load cyq chips:', error)
  } finally {
    chipLoading.value = false
  }
}

// 日期选择变化时加载对应日期的筹码分布
const onChipDateChange = (date) => {
  if (date) {
    loadCyqChips(date)
  } else {
    loadCyqChips()
  }
}

// 筹码集中度 = (有筹码的最高价 - 有筹码的最低价) / (有筹码的最高价 + 有筹码的最低价)
const chipConcentration = computed(() => {
  const chips = chipData.value?.chips
  if (!chips || chips.length === 0) return null
  const prices = chips.filter(c => c.percent > 0).map(c => c.price)
  if (prices.length === 0) return null
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  if (maxPrice + minPrice === 0) return null
  return ((maxPrice - minPrice) / (maxPrice + minPrice)) * 100
})

// 转发内部 StockChipChart 的 resize，供父组件窗口 resize 时调用
const resize = () => {
  chipChartRef.value?.resize()
}

defineExpose({ resize })

onMounted(() => {
  loadCyqChips()
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

/* 筹码分布 */
.chip-summary {
  display: flex;
  justify-content: space-around;
  padding: 10px 0 6px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 8px;
}

.chip-summary .summary-item {
  text-align: center;
}

.chip-summary .summary-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.chip-summary .summary-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
}
</style>
