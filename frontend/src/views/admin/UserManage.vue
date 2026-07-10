<template>
  <div class="user-manage-page">
    <el-card class="user-card">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" size="small" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>新增用户
          </el-button>
        </div>
      </template>

      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="phone" label="手机号" min-width="140" />

        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.role === 'admin'" type="danger" size="small">admin</el-tag>
            <el-tag v-else type="primary" size="small">user</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="has_totp" label="TOTP 已绑定" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.has_totp" type="success" size="small">已绑定</el-tag>
            <el-tag v-else type="info" size="small">未绑定</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success" size="small">启用</el-tag>
            <el-tag v-else type="info" size="small">禁用</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="invitation_code" label="邀请码" width="160">
          <template #default="{ row }">
            {{ row.invitation_code || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="last_login_at" label="最近登录" width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_login_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="resetTotp(row)">
              重置 TOTP
            </el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'info' : 'success'"
              @click="toggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="新增用户" width="400px">
      <el-form :model="newUser" label-width="80px">
        <el-form-item label="手机号" required>
          <el-input v-model="newUser.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="newUser.role">
            <el-radio label="user">普通用户</el-radio>
            <el-radio label="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createUser">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { authApi } from '@/api/auth'
import { Plus } from '@element-plus/icons-vue'

const users = ref([])
const loading = ref(false)

const showCreateDialog = ref(false)
const creating = ref(false)
const newUser = ref({ phone: '', role: 'user' })

onMounted(() => {
  fetchUsers()
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await authApi.listUsers()
    users.value = res.data
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  newUser.value = { phone: '', role: 'user' }
  showCreateDialog.value = true
}

const createUser = async () => {
  if (!newUser.value.phone.trim()) {
    ElMessage.warning('请输入手机号')
    return
  }

  creating.value = true
  try {
    const res = await authApi.createUser(newUser.value.phone, newUser.value.role)
    ElMessage.success(`邀请码：${res.data.invitation_code}`)
    showCreateDialog.value = false
    newUser.value = { phone: '', role: 'user' }
    await fetchUsers()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建用户失败')
  } finally {
    creating.value = false
  }
}

const resetTotp = async (row) => {
  try {
    const res = await authApi.updateUser(row.id, { reset_totp: true })
    ElMessage.success(`新邀请码：${res.data.invitation_code}`)
    await fetchUsers()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '重置 TOTP 失败')
  }
}

const toggleActive = async (row) => {
  try {
    await authApi.updateUser(row.id, { is_active: !row.is_active })
    await fetchUsers()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.user-manage-page {
  padding: 20px;
}

.user-card {
  max-width: 1200px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
