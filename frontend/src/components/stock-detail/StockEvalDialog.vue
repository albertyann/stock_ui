<template>
  <el-dialog v-model="visible" title="股票评估（RSI强势评分）" width="680px">
    <el-form label-width="80px">
      <el-form-item label="股票">
        <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
      </el-form-item>
      <el-form-item label="评估日期">
        <el-date-picker
          v-model="evalDate"
          type="date"
          placeholder="选择评估日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="说明">
        <el-text type="info" size="small">
          将使用 RSI强势策略引擎，计算评估日期往前 10 个交易日的评分。
        </el-text>
      </el-form-item>
    </el-form>

    <!-- 评分结果表格 -->
    <template v-if="scores.length > 0">
      <el-divider />
      <div class="eval-scores-section">
        <div class="eval-scores-header">
          评分结果（{{ scores.length }} 个交易日）
          <span class="golden-hint">日期标红 = MACD 金叉日</span>
        </div>
        <el-table :data="sortedEvalScores" size="small" border stripe max-height="320px">
          <el-table-column prop="date" label="日期" width="130">
            <template #default="{ row }">
              <span :class="{ 'macd-golden': goldenCrossDates.has(row.date) }">
                {{ row.date }}
                <el-tag
                  v-if="goldenCrossDates.has(row.date)"
                  type="danger"
                  size="small"
                  effect="dark"
                  class="golden-tag"
                >
                  金叉
                </el-tag>
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="评分" width="70">
            <template #default="{ row }">
              <el-tag v-if="row.score > 85" type="success" size="small" effect="dark">
                {{ row.score.toFixed(0) }}
              </el-tag>
              <span v-else :class="row.score > 0 ? '' : 'score-low'">
                {{ row.score != null ? row.score.toFixed(0) : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="passed_screen" label="通过" width="60" align="center">
            <template #default="{ row }">
              <el-icon v-if="row.passed_screen" color="#67c23a"><Check /></el-icon>
              <el-icon v-else color="#909399"><Close /></el-icon>
            </template>
          </el-table-column>
          <el-table-column prop="rsi12" label="RSI12" width="72">
            <template #default="{ row }">
              {{ row.rsi12 != null ? row.rsi12.toFixed(1) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="volume_ratio" label="量比" width="72">
            <template #default="{ row }">
              {{ row.volume_ratio != null ? row.volume_ratio.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="adx" label="ADX" width="72">
            <template #default="{ row }">
              {{ row.adx != null ? row.adx.toFixed(1) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="macd_hist" label="MACD柱" width="80">
            <template #default="{ row }">
              <span :style="{ color: row.macd_hist >= 0 ? '#f56c6c' : '#67c23a' }">
                {{ row.macd_hist != null ? row.macd_hist.toFixed(3) : '-' }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <template #footer>
      <el-button @click="visible = false" :disabled="loading">关闭</el-button>
      <el-button
        type="success"
        :loading="loading"
        :disabled="loading"
        @click="handleEvaluate"
      >
        开始评估
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Check, Close } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  stock: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  scores: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'evaluate'])

const visible = ref(false)
const evalDate = ref(loadSavedEvalDate())

// 弹窗内评分按日期降序（最新在前）
const sortedEvalScores = computed(() =>
  [...props.scores].reverse()
)

// MACD 金叉日期集合：DIF 自下而上穿 DEA 的交易日
// scores 为时间升序；金叉 = 当日 dif > dea 且前一交易日 dif <= dea
const goldenCrossDates = computed(() => {
  const crosses = new Set()
  const scores = props.scores
  for (let i = 1; i < scores.length; i++) {
    const prev = scores[i - 1]
    const cur = scores[i]
    if (
      cur.macd_dif != null && cur.macd_dea != null &&
      prev.macd_dif != null && prev.macd_dea != null &&
      cur.macd_dif > cur.macd_dea &&
      prev.macd_dif <= prev.macd_dea
    ) {
      crosses.add(cur.date)
    }
  }
  return crosses
})

// 从 localStorage 读取上次选中的评估日期
function loadSavedEvalDate() {
  try {
    const saved = localStorage.getItem('stockDetailEvalDate')
    if (saved) return saved
  } catch (error) {
    console.warn('Failed to load saved eval date:', error)
  }
  return new Date().toISOString().slice(0, 10)
}

// 评估日期变化时写入 localStorage
watch(evalDate, (newVal) => {
  if (newVal) {
    try {
      localStorage.setItem('stockDetailEvalDate', newVal)
    } catch (error) {
      console.warn('Failed to save eval date:', error)
    }
  }
})

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && !evalDate.value) {
    evalDate.value = new Date().toISOString().slice(0, 10)
  }
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

const handleEvaluate = () => {
  emit('evaluate', evalDate.value)
}
</script>

<style scoped>
/* 评估评分结果表格 */
.eval-scores-section {
  padding: 0 4px;
}

.eval-scores-header {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.score-low {
  color: var(--text-muted);
}

/* MACD 金叉日期标红 */
.macd-golden {
  color: #f56c6c;
  font-weight: bold;
}

.golden-tag {
  margin-left: 4px;
  transform: scale(0.85);
}

.golden-hint {
  margin-left: 12px;
  font-size: 12px;
  font-weight: normal;
  color: #f56c6c;
}
</style>
