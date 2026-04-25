<template>
  <div class="page-container">
    <div class="page-header">
      <h2>标签管理</h2>
      <el-button type="primary" @click="openCreateDialog">新建标签</el-button>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="标签名称">
          <el-input
            v-model="filter.name"
            placeholder="输入标签名称"
            clearable
            @keyup.enter="handleFilterChange"
            @clear="handleFilterChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="tableData" stripe border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="标签名称" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm
              title="确定删除这个标签吗？"
              @confirm="deleteTag(row)"
            >
              <template #reference>
                <el-button type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑标签' : '新建标签'"
      width="500px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="标签名称">
          <el-input v-model="form.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入标签描述，说明该标签的作用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { tagApi } from '@/api'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)

const filter = reactive({
  name: ''
})

const form = reactive({
  name: '',
  description: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

const loadData = async () => {
  loading.value = true
  try {
    const response = await tagApi.getAll({
      page: pagination.page,
      page_size: pagination.page_size,
      name: filter.name || null
    })
    if (response.success) {
      tableData.value = response.data
      pagination.total = response.pagination.total
      pagination.total_pages = response.pagination.total_pages
    }
  } catch (error) {
    console.error('Failed to load tags:', error)
    ElMessage.error('加载标签失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  loadData()
}

const resetFilter = () => {
  filter.name = ''
  pagination.page = 1
  loadData()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  loadData()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

const openCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  form.name = ''
  form.description = ''
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请输入标签名称')
    return
  }

  submitLoading.value = true
  try {
    if (isEdit.value) {
      const response = await tagApi.update(editingId.value, {
        name: form.name.trim(),
        description: form.description.trim() || null
      })
      if (response.success) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        loadData()
      }
    } else {
      const response = await tagApi.create({
        name: form.name.trim(),
        description: form.description.trim() || null
      })
      if (response.success) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        loadData()
      }
    }
  } catch (error) {
    console.error('Failed to save tag:', error)
    if (error.response?.status === 400) {
      ElMessage.error('标签名称已存在')
    } else {
      ElMessage.error('保存失败')
    }
  } finally {
    submitLoading.value = false
  }
}

const deleteTag = async (row) => {
  try {
    await tagApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    console.error('Failed to delete tag:', error)
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
