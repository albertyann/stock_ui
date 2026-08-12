<template>
  <!-- AI 调研记录 -->
  <el-card class="mt-20 stock-survey-card" v-loading="surveysLoading">
    <template #header>
      <div class="card-header">
        <span>AI 调研记录</span>
        <span class="signal-count" v-if="surveyList.length > 0">共 {{ surveyList.length }} 条</span>
      </div>
    </template>

    <div v-if="surveyList.length === 0" class="empty-signals">
      <el-empty description="暂无 AI 调研记录" :image-size="60" />
    </div>

    <el-timeline v-else>
      <el-timeline-item
        v-for="survey in surveyList"
        :key="survey.id"
        type="primary"
        :timestamp="formatDateTime(survey.created_at)"
        placement="top"
      >
        <div class="survey-timeline-content">
          <div v-if="survey.query" class="survey-query">
            问题：{{ survey.query }}
          </div>
          <div class="survey-result" v-html="renderSurveyContent(survey.content)"></div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { aiChatApi } from '@/api'

const props = defineProps({
  tsCode: {
    type: String,
    required: true
  }
})

const surveysLoading = ref(false)
const surveyList = ref([])

const loadSurveys = async () => {
  surveysLoading.value = true
  try {
    const response = await aiChatApi.getSurveys(props.tsCode)
    if (response.success) {
      surveyList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load surveys:', error)
  } finally {
    surveysLoading.value = false
  }
}

defineExpose({ reload: loadSurveys })

const renderSurveyContent = (content) => {
  if (!content) return ''
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

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
  loadSurveys()
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

.empty-signals {
  padding: 20px 0;
}

.stock-survey-card {
  max-height: 1000px;
  overflow-y: auto;
}

.survey-timeline-content {
  padding: 8px 0;
}

.survey-query {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding: 8px 10px;
  background-color: var(--bg-input);
  border-radius: 4px;
}

.survey-result {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  word-break: break-word;
}

.survey-result pre {
  background: var(--bg-input);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
}

.survey-result code {
  background: var(--bg-input);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}
</style>
