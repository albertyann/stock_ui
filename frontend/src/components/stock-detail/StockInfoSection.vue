<template>
  <el-card class="mt-20">
    <template #header>
      <div class="card-header">
        <span>股票信息</span>
        <el-button size="small" type="primary" link @click="openCreateInfoDialog">
          添加
        </el-button>
      </div>
    </template>

    <div class="stock-infos-list">
      <template v-if="stockInfos.length > 0">
        <div
          v-for="info in stockInfos"
          :key="info.id"
          class="stock-info-item"
        >
          <div class="info-content">{{ info.memo }}</div>
          <div class="info-actions">
            <el-button
              size="small"
              type="primary"
              link
              @click="openEditInfoDialog(info)"
            >
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button
              size="small"
              type="danger"
              link
              @click="deleteStockInfo(info.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </template>
      <el-text v-else type="info" size="small">暂无信息</el-text>
    </div>
  </el-card>

  <!-- 股票信息弹窗 -->
  <StockInfoDialog
    v-model="showInfoDialog"
    :stock="stock"
    :mode="infoDialogMode"
    :info="editingInfo"
    @saved="loadStockInfos"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { stockInfoApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import StockInfoDialog from '@/components/stock-detail/StockInfoDialog.vue'

const props = defineProps({
  tsCode: { type: String, required: true },
  stock: { type: Object, default: null }
})

const stockInfos = ref([])
const showInfoDialog = ref(false)
const infoDialogMode = ref('create')
const editingInfo = ref(null)

// 加载股票信息
const loadStockInfos = async () => {
  try {
    const response = await stockInfoApi.get(props.tsCode)
    if (response.success) {
      stockInfos.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load stock infos:', error)
  }
}

// 打开添加信息弹窗
const openCreateInfoDialog = () => {
  infoDialogMode.value = 'create'
  editingInfo.value = null
  showInfoDialog.value = true
}

// 打开编辑信息弹窗
const openEditInfoDialog = (info) => {
  infoDialogMode.value = 'edit'
  editingInfo.value = info
  showInfoDialog.value = true
}

// 删除股票信息
const deleteStockInfo = async (infoId) => {
  try {
    const response = await stockInfoApi.delete(infoId)
    if (response.success) {
      ElMessage.success('删除成功')
      await loadStockInfos()
    } else {
      ElMessage.error(response.error || '删除失败')
    }
  } catch (error) {
    console.error('Failed to delete stock info:', error)
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadStockInfos()
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

/* 股票信息列表 */
.stock-infos-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stock-info-item {
  position: relative;
  padding: 10px 12px;
  background-color: var(--bg-input);
  border-radius: 4px;
  transition: all 0.2s;
}

.stock-info-item:hover {
  background-color: var(--bg-hover);
}

.stock-info-item:hover .info-actions {
  opacity: 1;
}

.info-content {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.info-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}
</style>
