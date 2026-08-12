<template>
  <el-dialog v-model="visible" title="指标设置" width="420px">
    <el-form label-width="50px">
      <div class="indicator-group">
        <div class="indicator-group__header">
          <span class="indicator-group__title">MA</span>
          <el-button size="small" link @click="toggleMaGroup">
            {{ isAllMaSelected ? '取消全选' : '全选' }}
          </el-button>
        </div>
        <div class="indicator-group__items">
          <div
            v-for="item in maIndicatorOptions"
            :key="item.key"
            class="indicator-item"
          >
            <span
              class="indicator-color-dot"
              :style="{ backgroundColor: item.color }"
            ></span>
            <el-checkbox v-model="klineIndicatorSettingsDraft.ma[item.key]" size="small">
              {{ item.label }}
            </el-checkbox>
          </div>
        </div>
      </div>

      <div class="indicator-group">
        <div class="indicator-group__header">
          <span class="indicator-group__title">EMA</span>
          <el-button size="small" link @click="toggleEmaGroup">
            {{ isAllEmaSelected ? '取消全选' : '全选' }}
          </el-button>
        </div>
        <div class="indicator-group__items">
          <div
            v-for="item in emaIndicatorOptions"
            :key="item.key"
            class="indicator-item"
          >
            <span
              class="indicator-color-dot"
              :style="{ backgroundColor: item.color }"
            ></span>
            <el-checkbox v-model="klineIndicatorSettingsDraft.ema[item.key]" size="small">
              {{ item.label }}
            </el-checkbox>
          </div>
        </div>
      </div>

      <div class="indicator-group">
        <div class="indicator-group__header">
          <span class="indicator-group__title">BOLL</span>
        </div>
        <div class="indicator-group__items">
          <div class="indicator-item">
            <span class="indicator-color-dot" style="background-color: #409eff"></span>
            <span class="indicator-color-dot" style="background-color: #67c23a"></span>
            <span class="indicator-color-dot" style="background-color: #f56c6c"></span>
            <el-checkbox v-model="klineIndicatorSettingsDraft.boll" size="small">布林带</el-checkbox>
          </div>
        </div>
      </div>
    </el-form>

    <template #footer>
      <el-button size="small" @click="resetKlineIndicatorSettings">重置默认</el-button>
      <el-button size="small" @click="cancelKlineIndicatorDialog">取消</el-button>
      <el-button size="small" type="primary" @click="confirmKlineIndicatorDialog">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  settings: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const defaultKlineIndicatorSettings = {
  ma: { ma5: true, ma10: false, ma20: true, ma30: false, ma60: true, ma120: false },
  ema: { ema9: true, ema21: true },
  boll: false
}

const cloneIndicatorSettings = (settings) => JSON.parse(JSON.stringify(settings))

const visible = ref(false)
const klineIndicatorSettingsDraft = ref(cloneIndicatorSettings(props.settings))

const maIndicatorOptions = [
  { key: 'ma5', label: 'MA5', color: '#ee6666' },
  { key: 'ma10', label: 'MA10', color: '#fac858' },
  { key: 'ma20', label: 'MA20', color: '#3ba272' },
  { key: 'ma30', label: 'MA30', color: '#5470c6' },
  { key: 'ma60', label: 'MA60', color: '#ea7ccc' },
  { key: 'ma120', label: 'MA120', color: '#91cc75' }
]

const emaIndicatorOptions = [
  { key: 'ema9', label: 'EMA9', color: '#00d4aa' },
  { key: 'ema21', label: 'EMA21', color: '#9a60b4' }
]

const isAllMaSelected = computed(() =>
  maIndicatorOptions.every((item) => klineIndicatorSettingsDraft.value.ma[item.key])
)

const isAllEmaSelected = computed(() =>
  emaIndicatorOptions.every((item) => klineIndicatorSettingsDraft.value.ema[item.key])
)

// 同步 modelValue；打开时基于当前设置生成草稿
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    klineIndicatorSettingsDraft.value = cloneIndicatorSettings(props.settings)
  }
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

const confirmKlineIndicatorDialog = () => {
  emit('confirm', cloneIndicatorSettings(klineIndicatorSettingsDraft.value))
  visible.value = false
}

const cancelKlineIndicatorDialog = () => {
  visible.value = false
}

const resetKlineIndicatorSettings = () => {
  klineIndicatorSettingsDraft.value = cloneIndicatorSettings(defaultKlineIndicatorSettings)
}

const toggleMaGroup = () => {
  const next = !isAllMaSelected.value
  maIndicatorOptions.forEach((item) => {
    klineIndicatorSettingsDraft.value.ma[item.key] = next
  })
}

const toggleEmaGroup = () => {
  const next = !isAllEmaSelected.value
  emaIndicatorOptions.forEach((item) => {
    klineIndicatorSettingsDraft.value.ema[item.key] = next
  })
}
</script>

<style scoped>
/* 日K主图指标设置 */
.indicator-group {
  margin-bottom: 16px;
}

.indicator-group__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-left: 12px;
}

.indicator-group__title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.indicator-group__items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding-left: 12px;
}

.indicator-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.indicator-color-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.indicator-group :deep(.el-checkbox__label),
.indicator-item :deep(.el-checkbox__label) {
  font-size: 12px;
}
</style>
