<template>
  <div class="snapshot-manage">
    <div class="header-actions">
      <h2>快照管理</h2>
      <div class="header-right">
        <el-select
          v-model="selectedWatchlistId"
          placeholder="选择分组"
          style="width: 180px; margin-right: 10px;"
          @change="handleWatchlistChange"
        >
          <el-option
            v-for="wl in watchlists"
            :key="wl.id"
            :label="wl.name"
            :value="wl.id"
          />
        </el-select>
        <el-button type="warning" @click="handleCreateSnapshot" :loading="createLoading">
          <el-icon><Camera /></el-icon>创建快照
        </el-button>
      </div>
    </div>

    <el-table :data="snapshots" style="width: 100%" v-loading="loading">
      <el-table-column type="expand">
        <template #default="{ row }">
          <el-table :data="row.items" :border="true" size="small" style="margin: 10px;">
            <el-table-column prop="ts_code" label="股票代码" width="120" />
            <el-table-column prop="name" label="股票名称" width="120" />
            <el-table-column prop="industry" label="板块" width="150" />
            <el-table-column prop="notes" label="备注" show-overflow-tooltip />
          </el-table>
        </template>
      </el-table-column>
      <el-table-column prop="snapshot_date" label="快照日期" width="120" />
      <el-table-column prop="snapshot_time" label="快照时间" width="120" />
      <el-table-column label="股票数量" width="100">
        <template #default="{ row }">
          {{ row.items?.length || 0 }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="danger" size="small" link @click="handleDeleteSnapshot(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !snapshots.length" description="暂无快照数据" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { storeToRefs } from 'pinia'
import { watchlistApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = useWatchlistStore()
const { watchlists } = storeToRefs(store)

const selectedWatchlistId = ref(null)
const snapshots = ref([])
const loading = ref(false)
const createLoading = ref(false)

// 默认选中 id=2（开票盯股票），如果没有则选中第一个
const initDefaultWatchlist = () => {
  if (watchlists.value?.length) {
    const defaultWl = watchlists.value.find(w => w.id === 2)
    selectedWatchlistId.value = defaultWl ? defaultWl.id : watchlists.value[0].id
  }
}

onMounted(async () => {
  await store.fetchWatchlists()
  initDefaultWatchlist()
  if (selectedWatchlistId.value) {
    await loadSnapshots()
  }
})

watch(() => watchlists.value, () => {
  if (!selectedWatchlistId.value && watchlists.value?.length) {
    initDefaultWatchlist()
    loadSnapshots()
  }
})

const handleWatchlistChange = async () => {
  await loadSnapshots()
}

const loadSnapshots = async () => {
  if (!selectedWatchlistId.value) return
  loading.value = true
  try {
    const response = await watchlistApi.getSnapshots(selectedWatchlistId.value)
    snapshots.value = response.data || []
  } catch (error) {
    console.error('Failed to load snapshots:', error)
    ElMessage.error('加载快照失败')
    snapshots.value = []
  } finally {
    loading.value = false
  }
}

const handleCreateSnapshot = async () => {
  if (!selectedWatchlistId.value) {
    ElMessage.warning('请先选择分组')
    return
  }

  createLoading.value = true
  try {
    // 获取当前分组的股票列表
    const response = await watchlistApi.getStocksByWatchDate(selectedWatchlistId.value)
    const stocks = response.data?.stocks || []

    if (!stocks.length) {
      ElMessage.warning('当前分组没有股票，无法创建快照')
      createLoading.value = false
      return
    }

    const stocksToSnapshot = stocks.map(stock => ({
      ts_code: stock.ts_code,
      name: stock.name || stock.symbol,
      industry: stock.industry || '',
      notes: stock.notes || ''
    }))

    await watchlistApi.createSnapshot(selectedWatchlistId.value, stocksToSnapshot)
    ElMessage.success(`成功创建快照，共 ${stocksToSnapshot.length} 只股票`)
    await loadSnapshots()
  } catch (error) {
    console.error('Failed to create snapshot:', error)
    ElMessage.error('创建快照失败')
  } finally {
    createLoading.value = false
  }
}

const handleDeleteSnapshot = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.snapshot_date} ${row.snapshot_time} 的快照吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await watchlistApi.deleteSnapshot(selectedWatchlistId.value, row.id)
    ElMessage.success('删除成功')
    await loadSnapshots()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete snapshot:', error)
      ElMessage.error('删除失败')
    }
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}
</script>

<style scoped>
.snapshot-manage {
  padding: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions h2 {
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}
</style>
