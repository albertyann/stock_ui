<template>
  <el-dialog v-model="visible" title="编辑标签" width="500px">
    <el-form label-width="100px">
      <el-form-item label="股票">
        <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
      </el-form-item>
      <el-form-item label="已选标签">
        <div class="selected-tags-container">
          <el-tag
            v-for="tag in popoverSelectedTags"
            :key="tag"
            closable
            size="small"
            @close="removeSelectedTag(tag)"
            class="selected-tag"
          >
            {{ tag }}
          </el-tag>
          <el-input
            ref="tagInputRef"
            v-model="newTagInput"
            size="small"
            class="tag-input"
            placeholder="输入新标签，回车添加"
            @keydown.enter.prevent="addNewTag"
          />
        </div>
      </el-form-item>
      <el-form-item label="可选标签">
        <div class="available-tags-container">
          <el-tag
            v-for="tag in availableTagsList"
            :key="tag"
            size="small"
            effect="plain"
            class="available-tag"
            @click="addSelectedTag(tag)"
          >
            {{ tag }}
          </el-tag>
          <el-text v-if="availableTagsList.length === 0" type="info" size="small">
            暂无可选标签
          </el-text>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        @click="saveStockTags"
      >
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { stockApi, signalApi, watchlistApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  tsCode: {
    type: String,
    default: ''
  },
  stock: {
    type: Object,
    default: null
  },
  tags: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const visible = ref(false)
const allTags = ref([])
const popoverSelectedTags = ref([])
const newTagInput = ref('')
const tagInputRef = ref(null)

// 可选标签列表（排除已选中的）
const availableTagsList = computed(() => {
  return allTags.value.filter(tag => !popoverSelectedTags.value.includes(tag))
})

// 同步 modelValue；打开时初始化已选标签并加载可选标签
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    popoverSelectedTags.value = [...props.tags]
    newTagInput.value = ''
    loadAllTags()
  }
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

// 加载所有可用标签
const loadAllTags = async () => {
  try {
    const response = await watchlistApi.getAllTags()
    if (response.success) {
      allTags.value = response.data?.tags || []
    }
  } catch (error) {
    console.error('Failed to load all tags:', error)
  }
}

// 添加新标签（通过输入框）
const addNewTag = () => {
  const tag = newTagInput.value.trim()
  if (tag && !popoverSelectedTags.value.includes(tag)) {
    popoverSelectedTags.value.push(tag)
  }
  newTagInput.value = ''
}

// 添加已有标签（点击可选标签）
const addSelectedTag = (tag) => {
  if (!popoverSelectedTags.value.includes(tag)) {
    popoverSelectedTags.value.push(tag)
  }
}

// 移除已选标签
const removeSelectedTag = (tag) => {
  const index = popoverSelectedTags.value.indexOf(tag)
  if (index > -1) {
    popoverSelectedTags.value.splice(index, 1)
  }
}

// 保存股票标签
const saveStockTags = async () => {
  try {
    // 计算新增的标签
    const newTags = popoverSelectedTags.value.filter(tag => !props.tags.includes(tag))

    const response = await stockApi.updateTags(props.tsCode, popoverSelectedTags.value)
    if (response.success) {
      visible.value = false
      ElMessage.success('标签更新成功')
      await loadAllTags()

      // 如果有新增标签，发送 ADD_TAG 信号
      let signal = null
      if (newTags.length > 0) {
        const signalResponse = await signalApi.addTag(props.tsCode, newTags)
        if (signalResponse.success) {
          signal = {
            id: signalResponse.data?.id || Date.now(),
            ts_code: props.tsCode,
            signal_type: 'ADD_TAG',
            note_content: newTags.join(', '),
            created_at: new Date().toISOString(),
            signal_date: new Date().toISOString()
          }
        }
      }

      emit('saved', {
        selectedTags: [...popoverSelectedTags.value],
        signal
      })
    } else {
      ElMessage.error(response.error || '标签更新失败')
    }
  } catch (error) {
    console.error('Failed to save tags:', error)
    ElMessage.error('标签更新失败')
  }
}
</script>

<style scoped>
/* 已选标签容器 */
.selected-tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 8px;
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  min-height: 32px;
  width: 100%;
}

.selected-tag {
  margin: 0;
}

.tag-input {
  width: 120px;
  flex-shrink: 1;
}

.tag-input :deep(.el-input__wrapper) {
  box-shadow: none;
}

/* 可选标签容器 */
.available-tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.available-tag {
  margin: 0;
  cursor: pointer;
  transition: all 0.2s;
}

.available-tag:hover {
  color: var(--accent);
  border-color: var(--accent);
  background-color: var(--bg-hover);
}
</style>
