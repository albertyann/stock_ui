<template>
  <!-- 信号时间线 -->
  <el-card class="mt-20 signal-timeline-card" v-loading="signalsLoading">
    <template #header>
      <div class="card-header">
        <span>信号记录</span>
        <div class="header-actions">
          <span class="signal-count" v-if="signalList.length > 0">共 {{ signalList.length }} 条</span>
          <el-button size="small" type="primary" link @click="emit('open-notes')">
            <el-icon><EditPen /></el-icon>备注
          </el-button>
        </div>
      </div>
    </template>

    <div v-if="signalList.length === 0" class="empty-signals">
      <el-empty description="暂无信号记录" :image-size="60" />
    </div>

    <el-timeline v-else>
      <el-timeline-item
        v-for="signal in signalList"
        :key="signal.id"
        :type="getSignalTimelineType(signal.signal_type)"
        :timestamp="formatDateTime(signal.created_at || signal.signal_date)"
        placement="top"
      >
        <div class="signal-timeline-content">
          <div class="signal-timeline-header">
            <el-tag size="small" :type="getSignalType(signal.signal_type)">
              {{ formatSignal(signal.signal_type) }}
            </el-tag>
            <span v-if="signal.signal_strength" class="signal-strength">
              强度: {{ signal.signal_strength }}
            </span>
          </div>

          <!-- NOTE 类型展示 note_content -->
          <div v-if="signal.signal_type === 'NOTE'" class="signal-note">
            {{ signal.note_content || '无内容' }}
          </div>

          <!-- ADD_TAG 类型展示标签列表 -->
          <div v-else-if="signal.signal_type === 'ADD_TAG'" class="signal-tags">
            <el-tag
              v-for="tag in (signal.note_content || '').split(', ')"
              :key="tag"
              size="small"
              effect="plain"
            >
              {{ tag }}
            </el-tag>
          </div>

          <!-- 其他类型展示 execution_result -->
          <div v-else class="signal-result">
            <div v-if="signal.execution_result" class="result-text">
              {{ signal.execution_result }}
            </div>
            <div v-else class="result-empty">
              信号产生时价格: ¥{{ signal.current_price?.toFixed(2) || '-' }}
            </div>
          </div>

          <div v-if="signal.indicators" class="signal-indicators-mini">
            <el-tag size="small" type="info" v-if="signal.indicators.ma20">
              MA20: {{ signal.indicators.ma20.toFixed(2) }}
            </el-tag>
            <el-tag size="small" type="info" v-if="signal.indicators.macd">
              MACD: {{ signal.indicators.macd.toFixed(2) }}
            </el-tag>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { signalApi } from '@/api'
import { EditPen } from '@element-plus/icons-vue'
import { getSignalType, getSignalTimelineType, formatSignal } from '@/utils/stock'

const props = defineProps({
  tsCode: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['open-notes'])

const signalsLoading = ref(false)
const signalList = ref([])

const loadSignals = async () => {
  signalsLoading.value = true
  try {
    const response = await signalApi.getAll({
      ts_code: props.tsCode,
      active_only: false,
      limit: 100
    })
    if (response.success) {
      signalList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load signals:', error)
  } finally {
    signalsLoading.value = false
  }
}

// 备注/标签保存后由父组件追加新信号
const addSignal = (signal) => {
  if (signal) {
    signalList.value.unshift(signal)
  }
}

defineExpose({ addSignal, reload: loadSignals })

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-')
}

onMounted(() => {
  loadSignals()
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

.signal-count {
  font-size: 12px;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.empty-signals {
  padding: 20px 0;
}

/* 信号时间线样式 */
.signal-timeline-card {
  height: 480px;
  overflow-y: auto;
}

.signal-timeline-content {
  padding: 8px 0;
}

.signal-timeline-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.signal-strength {
  font-size: 12px;
  color: var(--text-secondary);
}

.signal-note {
  padding: 10px 12px;
  background-color: var(--bg-input);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.signal-tags {
  padding: 10px 12px;
  background-color: var(--bg-input);
  border-radius: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.signal-result {
  padding: 10px 12px;
  background-color: var(--bg-input);
  border-radius: 4px;
}

.result-text {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-empty {
  color: var(--text-muted);
  font-size: 13px;
  font-style: italic;
}

.signal-indicators-mini {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}
</style>
