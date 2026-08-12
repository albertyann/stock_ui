<template>
  <el-dialog v-model="visible" title="编辑股票备注" width="500px" @opened="onDialogOpened">
    <el-form label-width="100px">
      <el-form-item label="股票">
        <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
      </el-form-item>
      <el-form-item label="备注">
        <el-input
          ref="notesInputRef"
          v-model="stockNotesInput"
          type="textarea"
          :rows="4"
          placeholder="请输入股票备注信息..."
          resize="none"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        @click="saveStockNotes"
        :disabled="notesLoading"
        :loading="notesLoading"
      >
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { signalApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  stock: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const visible = ref(false)
const stockNotesInput = ref('')
const notesLoading = ref(false)
const notesInputRef = ref(null)

// 同步 modelValue；打开时清空输入
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    stockNotesInput.value = ''
  }
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

// Ctrl+Enter 快捷键提交
const handleKeydown = (e) => {
  if (e.ctrlKey && e.key === 'Enter' && visible.value && stockNotesInput.value.trim() && !notesLoading.value) {
    e.preventDefault()
    saveStockNotes()
  }
}
onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))

// 弹窗打开动画结束后聚焦输入框
const onDialogOpened = () => {
  notesInputRef.value?.focus()
}

const saveStockNotes = async () => {
  if (!props.stock || !props.stock.ts_code) return

  notesLoading.value = true
  const notesContent = stockNotesInput.value.trim()
  try {
    const response = await signalApi.addNote(props.stock.ts_code, notesContent)
    if (response.success) {
      visible.value = false

      emit('saved', {
        signal: {
          id: response.data?.id || Date.now(),
          ts_code: props.stock.ts_code,
          signal_type: 'NOTE',
          note_content: notesContent,
          created_at: new Date().toISOString(),
          signal_date: new Date().toISOString()
        },
        notes: notesContent
      })

      ElMessage.success('备注添加成功')
    } else {
      ElMessage.error(response.error || '备注更新失败')
    }
  } catch (error) {
    console.error('Failed to update stock notes:', error)
    ElMessage.error('备注更新失败')
  } finally {
    notesLoading.value = false
  }
}
</script>
