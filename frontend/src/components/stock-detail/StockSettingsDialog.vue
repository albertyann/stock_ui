<template>
  <el-dialog v-model="visible" title="设置" width="500px">
    <el-form label-width="100px">
      <el-form-item label="股票">
        <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
      </el-form-item>
      <el-form-item label="数据同步">
        <div class="sync-kline-section">
          <div class="sync-kline-desc">
            删除当前股票已有K线数据，从2018年至今全量重新拉取日线数据。
          </div>
          <el-button
            type="danger"
            :loading="syncKlineLoading"
            :disabled="syncKlineLoading"
            @click="handleSyncKline"
          >
            同步K线数据
          </el-button>
          <div v-if="syncKlineResult" class="sync-result" :class="syncKlineResult.success ? 'sync-success' : 'sync-error'">
            {{ syncKlineResult.success
              ? `同步完成：删除日线 ${syncKlineResult.deleted_daily || 0} 条，周线 ${syncKlineResult.deleted_weekly || 0} 条`
              : `同步失败：${syncKlineResult.error}`
            }}
          </div>
        </div>
      </el-form-item>
      <el-form-item label="删除股票">
        <div class="delete-stock-section">
          <div class="delete-stock-desc">
            将当前股票从关注列表中移除。
          </div>
          <el-button
            type="danger"
            :loading="deleteStockLoading"
            :disabled="deleteStockLoading || !watchlistStockInfo"
            @click="handleDeleteStock"
          >
            取消关注
          </el-button>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { stockApi, watchlistApi } from '@/api'

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
  watchlistStockInfo: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'kline-synced'])

const router = useRouter()

const visible = ref(false)
const syncKlineLoading = ref(false)
const syncKlineResult = ref(null)
const deleteStockLoading = ref(false)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

const handleSyncKline = async () => {
  syncKlineLoading.value = true
  syncKlineResult.value = null
  try {
    const response = await stockApi.syncKline(props.tsCode)
    syncKlineResult.value = response
    if (response.success) {
      ElMessage.success('K线数据同步完成')
      emit('kline-synced')
    } else {
      ElMessage.error(response.error || '同步失败')
    }
  } catch (error) {
    console.error('Failed to sync kline:', error)
    syncKlineResult.value = { success: false, error: error.message || '请求失败' }
    ElMessage.error('同步请求失败')
  } finally {
    syncKlineLoading.value = false
  }
}

const handleDeleteStock = async () => {
  if (!props.watchlistStockInfo) return
  deleteStockLoading.value = true
  try {
    await watchlistApi.removeStock(
      props.watchlistStockInfo.watchlist_id,
      props.watchlistStockInfo.id
    )
    ElMessage.success('删除成功')
    visible.value = false
    router.push({ path: '/watchlist' })
  } catch (error) {
    console.error('Failed to delete stock:', error)
    ElMessage.error('删除失败')
  } finally {
    deleteStockLoading.value = false
  }
}
</script>

<style scoped>
.sync-kline-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sync-kline-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

.sync-result {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 4px;
  line-height: 1.5;
}

.sync-result.sync-success {
  background-color: var(--bg-input);
  color: var(--stock-down);
}

.sync-result.sync-error {
  background-color: var(--bg-input);
  color: var(--stock-up);
}

.delete-stock-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.delete-stock-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}
</style>
