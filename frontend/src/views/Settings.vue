<template>
  <div class="settings-page">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>自选股分组管理</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>新建分组
          </el-button>
        </div>
      </template>
      
      <el-table :data="watchlists" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="分组名称" min-width="150">
          <template #default="{ row }">
            <div class="watchlist-name">
              <el-icon><Folder /></el-icon>
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="sort_num" label="排序" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.sort_num"
              :min="0"
              :max="9999"
              :controls="false"
              size="small"
              style="width: 80px"
              @change="handleSortChange(row)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              text
              @click="$router.push(`/watchlist/${row.id}`)"
            >
              查看
            </el-button>
            <el-button 
              type="primary" 
              size="small" 
              text
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              text
              :disabled="row.is_default"
              @click="confirmDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建分组对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建分组" width="400px">
      <el-form :model="newWatchlist" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="newWatchlist.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number
            v-model="newWatchlist.sort_num"
            :min="0"
            :max="9999"
            :controls="false"
            placeholder="请输入排序数字"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="newWatchlist.description" 
            type="textarea" 
            placeholder="请输入描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createWatchlist" :loading="creating">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑分组对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑分组" width="400px">
      <el-form :model="editWatchlist" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="editWatchlist.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number
            v-model="editWatchlist.sort_num"
            :min="0"
            :max="9999"
            :controls="false"
            placeholder="请输入排序数字"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="editWatchlist.description" 
            type="textarea" 
            placeholder="请输入描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateWatchlist" :loading="updating">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Folder } from '@element-plus/icons-vue'

const store = useWatchlistStore()
const { watchlists, loading } = storeToRefs(store)

const showCreateDialog = ref(false)
const creating = ref(false)
const newWatchlist = ref({ name: '', description: '', sort_num: 0 })

const showEditDialog = ref(false)
const updating = ref(false)
const editWatchlist = ref({ id: null, name: '', description: '', sort_num: 0 })

onMounted(() => {
  store.fetchWatchlists()
})

const createWatchlist = async () => {
  if (!newWatchlist.value.name.trim()) {
    ElMessage.warning('请输入分组名称')
    return
  }
  
  creating.value = true
  try {
    await store.createWatchlist(newWatchlist.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    newWatchlist.value = { name: '', description: '', sort_num: 0 }
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

const confirmDelete = (watchlist) => {
  if (watchlist.is_default) {
    ElMessage.warning('默认分组不能删除')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除分组 "${watchlist.name}" 吗？\n删除后该分组中的股票也将被移除。`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(() => {
      deleteWatchlist(watchlist.id)
    })
    .catch(() => {})
}

const deleteWatchlist = async (id) => {
  try {
    await store.deleteWatchlist(id)
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const openEditDialog = (watchlist) => {
  editWatchlist.value = {
    id: watchlist.id,
    name: watchlist.name,
    description: watchlist.description || '',
    sort_num: watchlist.sort_num || 0
  }
  showEditDialog.value = true
}

const updateWatchlist = async () => {
  if (!editWatchlist.value.name.trim()) {
    ElMessage.warning('请输入分组名称')
    return
  }

  updating.value = true
  try {
    const { id, ...data } = editWatchlist.value
    await store.updateWatchlist(id, data)
    ElMessage.success('修改成功')
    showEditDialog.value = false
    editWatchlist.value = { id: null, name: '', description: '', sort_num: 0 }
  } catch (error) {
    ElMessage.error('修改失败')
  } finally {
    updating.value = false
  }
}

// 处理表格内排序数字变化
const handleSortChange = async (row) => {
  try {
    const { id, name, description, sort_num } = row
    await store.updateWatchlist(id, { name, description, sort_num })
    ElMessage.success('排序已更新')
  } catch (error) {
    ElMessage.error('排序更新失败')
    // 重新获取数据以恢复原始值
    store.fetchWatchlists()
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.settings-page {
  padding: 20px;
}

h2 {
  margin: 0 0 20px 0;
  color: #303133;
}

.settings-card {
  max-width: 1200px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watchlist-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.watchlist-name .el-icon {
  color: #409EFF;
}
</style>
