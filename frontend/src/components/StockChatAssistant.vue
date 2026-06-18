<template>
  <div class="stock-chat-assistant">
    <!-- 浮动图标 -->
    <div
      v-if="!isOpen"
      class="chat-fab"
      @click="openChat"
    >
      <el-icon><ChatDotRound /></el-icon>
    </div>

    <!-- 聊天对话框 -->
    <div v-else class="chat-dialog">
      <div class="chat-header">
        <div class="chat-title">
          <el-icon><ChatDotRound /></el-icon>
          <span>股票助手</span>
        </div>
        <div class="chat-actions">
          <el-button size="small" link @click="closeChat">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <div ref="messagesRef" class="chat-messages">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['chat-message', msg.role === 'user' ? 'message-user' : 'message-assistant']"
        >
          <div class="message-bubble">
            <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
            <div v-if="msg.role === 'assistant'" class="message-actions">
              <el-button
                size="small"
                link
                :icon="CopyDocument"
                @click="copyContent(msg.content)"
              >
                复制
              </el-button>
              <el-button
                size="small"
                link
                :icon="DocumentChecked"
                @click="saveSurvey(msg)"
                :loading="savingIndex === index"
              >
                保存
              </el-button>
            </div>
          </div>
        </div>
        <div v-if="loading" class="chat-message message-assistant">
          <div class="message-bubble">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span style="margin-left: 8px;">思考中...</span>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题，例如：分析这只股票的走势"
          resize="none"
          @keydown.enter.prevent="sendMessage"
        />
        <el-button
          type="primary"
          class="send-button"
          :disabled="!inputMessage.trim() || loading"
          @click="sendMessage"
        >
          <el-icon><Promotion /></el-icon>
        </el-button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound,
  Close,
  Loading,
  Promotion,
  CopyDocument,
  DocumentChecked,
} from '@element-plus/icons-vue'
import { aiChatApi } from '@/api'

const props = defineProps({
  tsCode: {
    type: String,
    required: true,
  },
  stock: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['survey-saved'])

const isOpen = ref(false)
const inputMessage = ref('')
const messages = ref([])
const loading = ref(false)
const savingIndex = ref(null)
const messagesRef = ref(null)

const stockContext = computed(() => {
  const s = props.stock || {}
  return {
    ts_code: props.tsCode,
    name: s.name,
    industry: s.industry,
    current_price: s.current_price,
    change_pct: s.change_pct,
    pe: s.pe,
    pb: s.pb,
    market_cap: s.market_cap,
  }
})

const openChat = () => {
  isOpen.value = true
}

const closeChat = () => {
  isOpen.value = false
}

const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const response = await aiChatApi.chat({
      ts_code: props.tsCode,
      message: text,
      stock_context: stockContext.value,
    })

    if (response.success) {
      messages.value.push({ role: 'assistant', content: response.data, query: text })
    } else {
      messages.value.push({
        role: 'assistant',
        content: `请求失败：${response.error || '未知错误'}`,
        isError: true,
      })
    }
  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      role: 'assistant',
      content: '请求失败，请检查网络或 AI 配置。',
      isError: true,
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const copyContent = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    console.error('Copy failed:', error)
    ElMessage.error('复制失败')
  }
}

const saveSurvey = async (msg) => {
  const index = messages.value.indexOf(msg)
  if (index === -1) return
  savingIndex.value = index
  try {
    const response = await aiChatApi.saveSurvey({
      ts_code: props.tsCode,
      query: msg.query || '',
      content: msg.content,
      source: 'ai_chat',
    })
    if (response.success) {
      ElMessage.success('已保存到 stock_survey')
      emit('survey-saved')
    } else {
      ElMessage.error(response.error || '保存失败')
    }
  } catch (error) {
    console.error('Save survey error:', error)
    ElMessage.error('保存失败')
  } finally {
    savingIndex.value = null
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const renderMarkdown = (content) => {
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

watch(messages, scrollToBottom, { deep: true })
</script>

<style scoped>
.stock-chat-assistant {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1000;
}

.chat-fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transition: all 0.3s ease;
}

.chat-fab:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5);
}

.chat-dialog {
  width: 380px;
  height: 520px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  padding: 14px 16px;
  background: #409eff;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.chat-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chat-actions .el-button {
  color: #fff;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
}

.chat-message {
  margin-bottom: 16px;
  display: flex;
}

.message-user {
  justify-content: flex-end;
}

.message-assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}

.message-user .message-bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-assistant .message-bubble {
  background: #fff;
  color: #303133;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message-actions {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
}

.chat-input-area {
  padding: 12px;
  background: #fff;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chat-input-area .el-textarea {
  flex: 1;
}

.send-button {
  height: 52px;
  width: 52px;
}

:deep(.chat-input-area .el-textarea__inner) {
  resize: none;
}

:deep(.message-content pre) {
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
}

:deep(.message-content code) {
  background: #f5f7fa;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}
</style>
