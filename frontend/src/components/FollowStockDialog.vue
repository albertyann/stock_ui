<template>
  <el-dialog
    v-model="visible"
    title="关注股票"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="stock" class="follow-dialog-content">
      <div class="stock-basic-info">
        <h4>股票信息</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="股票代码">
            {{ stock.ts_code }}
          </el-descriptions-item>
          <el-descriptions-item label="名称">
            {{ stock.name }}
          </el-descriptions-item>
          <el-descriptions-item label="板块">
            {{ stock.industry || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="当前价格">
            ¥{{ (stock.price ?? 0).toFixed(2) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="follow-form">
        <h4>关注设置</h4>
        <el-form :model="form" label-width="100px">
          <el-form-item label="分组" required>
            <el-select
              v-model="form.watchlist_id"
              placeholder="请选择分组"
              style="width: 100%"
            >
              <el-option
                v-for="item in watchlistOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="关注理由" required>
            <el-select
              v-model="form.watch_reason"
              placeholder="请选择关注理由"
              style="width: 100%"
              allow-create
              filterable
            >
              <el-option
                v-for="reason in watchReasons"
                :key="reason.value"
                :label="reason.label"
                :value="reason.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="关注日期">
            <el-date-picker
              v-model="form.watch_date"
              type="date"
              placeholder="选择关注日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledDate"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="form.notes"
              type="textarea"
              :rows="3"
              placeholder="请填写备注信息"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button
        type="primary"
        :loading="loading"
        @click="confirmFollow"
      >
        确认关注
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
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const loading = ref(false)
const form = ref({
  watchlist_id: null,
  watch_reason: '',
  watch_date: '',
  notes: ''
})
const watchReasons = ref([])
const watchlistOptions = ref([])

// 同步 modelValue
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.stock) {
    resetForm()
    loadData()
  }
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

// 获取今日日期
const getTodayDate = () => {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

// 禁用未来日期
const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

// 重置表单
const resetForm = () => {
  form.value = {
    watchlist_id: null,
    watch_reason: '',
    watch_date: getTodayDate(),
    notes: ''
  }
}

// 加载数据
const loadData = async () => {
  await Promise.all([loadWatchReasons(), loadWatchlistOptions()])
}

// 加载关注原因列表
const loadWatchReasons = async () => {
  try {
    const response = await watchlistApi.getWatchReasons(8)
    if (response.data?.watch_reasons) {
      watchReasons.value = response.data.watch_reasons
    }
  } catch (error) {
    console.error('Failed to load watch reasons:', error)
  }
}

// 加载分组列表
const loadWatchlistOptions = async () => {
  try {
    const response = await watchlistApi.getAll()
    if (response.data) {
      watchlistOptions.value = response.data
    }
  } catch (error) {
    console.error('Failed to load watchlist options:', error)
  }
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 确认关注
const confirmFollow = async () => {
  if (!form.value.watchlist_id) {
    ElMessage.warning('请选择分组')
    return
  }
  if (!form.value.watch_reason) {
    ElMessage.warning('请填写关注理由')
    return
  }

  loading.value = true
  try {
    await watchlistApi.addStock(form.value.watchlist_id, {
      ts_code: props.stock.ts_code,
      watch_reason: form.value.watch_reason,
      watch_date: form.value.watch_date,
      notes: form.value.notes
    })
    ElMessage.success(`${props.stock.name} (${props.stock.ts_code}) 已添加到关注列表`)
    emit('success')
    handleClose()
  } catch (error) {
    console.error('Follow failed:', error)
    ElMessage.error('关注失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.follow-dialog-content {
  padding: 0 10px;
}

.stock-basic-info {
  margin-bottom: 24px;
}

.stock-basic-info h4,
.follow-form h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
  border-left: 4px solid #409eff;
  padding-left: 8px;
}

.follow-form {
  margin-top: 20px;
}

.follow-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.follow-form :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}
</style>
