<template>
  <el-dialog v-model="visible" title="切换分组" width="500px">
    <el-form label-width="100px">
      <el-form-item label="股票">
        <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
      </el-form-item>
      <el-form-item label="当前分组">
        <el-text>{{ watchlistStockInfo?.watchlist_name }}</el-text>
      </el-form-item>
      <el-form-item label="目标分组" required>
        <el-select
          v-model="selectedTargetWatchlist"
          placeholder="选择目标分组"
          style="width: 100%"
        >
          <el-option
            v-for="wl in availableWatchlists"
            :key="wl.id"
            :label="wl.name"
            :value="wl.id"
            :disabled="wl.id === watchlistStockInfo?.watchlist_id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="变更理由" required>
        <el-input
          v-model="switchGroupReason"
          type="textarea"
          :rows="3"
          placeholder="请填写变更理由（必填）"
          resize="none"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        @click="switchStockGroup"
        :disabled="!selectedTargetWatchlist || !switchGroupReason.trim() || switchLoading"
        :loading="switchLoading"
      >
        确认切换
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { watchlistApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  stock: {
    type: Object,
    default: null
  },
  watchlistStockInfo: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'switched'])

const visible = ref(false)
const selectedTargetWatchlist = ref(null)
const switchGroupReason = ref('')
const switchLoading = ref(false)
const availableWatchlists = ref([])

// 同步 modelValue；打开时重置表单并加载分组选项
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    selectedTargetWatchlist.value = null
    switchGroupReason.value = ''
    fetchWatchlistOptions()
  }
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

// 获取所有分组选项
const fetchWatchlistOptions = async () => {
  try {
    const response = await watchlistApi.getAll()
    if (response.success) {
      availableWatchlists.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to fetch watchlists:', error)
  }
}

// 切换股票分组
const switchStockGroup = async () => {
  if (!props.watchlistStockInfo || !selectedTargetWatchlist.value) return
  if (!switchGroupReason.value.trim()) {
    ElMessage.warning('请填写变更理由')
    return
  }

  switchLoading.value = true
  try {
    await watchlistApi.moveStockToWatchlist(
      props.watchlistStockInfo.id,
      selectedTargetWatchlist.value,
      switchGroupReason.value.trim()
    )
    ElMessage.success('切换分组成功')
    visible.value = false
    emit('switched')
  } catch (error) {
    console.error('Failed to switch stock group:', error)
    ElMessage.error('切换分组失败')
  } finally {
    switchLoading.value = false
  }
}
</script>
