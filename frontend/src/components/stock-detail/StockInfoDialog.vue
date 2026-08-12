<template>
  <el-dialog v-model="visible" :title="mode === 'create' ? '添加信息' : '编辑信息'" width="500px">
    <el-form label-width="100px">
      <el-form-item label="股票">
        <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
      </el-form-item>
      <el-form-item label="信息内容">
        <el-input
          v-model="infoMemoInput"
          type="textarea"
          :rows="4"
          placeholder="请输入股票相关信息..."
          resize="none"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        @click="saveStockInfo"
        :disabled="infoLoading"
        :loading="infoLoading"
      >
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { stockInfoApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  stock: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create'
  },
  info: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const visible = ref(false)
const infoMemoInput = ref('')
const infoLoading = ref(false)

// 同步 modelValue；打开时按模式初始化内容
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    infoMemoInput.value = props.mode === 'edit' ? (props.info?.memo || '') : ''
  }
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

// 保存股票信息
const saveStockInfo = async () => {
  if (!props.stock || !props.stock.ts_code) return

  infoLoading.value = true
  const memoContent = infoMemoInput.value.trim()

  try {
    let response
    if (props.mode === 'create') {
      response = await stockInfoApi.create({ ts_code: props.stock.ts_code, memo: memoContent })
    } else {
      response = await stockInfoApi.update(props.info?.id, { memo: memoContent })
    }

    if (response.success) {
      visible.value = false
      ElMessage.success(props.mode === 'create' ? '信息添加成功' : '信息更新成功')
      emit('saved')
    } else {
      ElMessage.error(response.error || '保存失败')
    }
  } catch (error) {
    console.error('Failed to save stock info:', error)
    ElMessage.error('保存失败')
  } finally {
    infoLoading.value = false
  }
}
</script>
