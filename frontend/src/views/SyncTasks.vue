<template>
  <div class="page-container">
    <div class="page-header">
      <h2>同步任务管理</h2>
      <el-button type="primary" @click="openEnableDialog">
        <el-icon><Plus /></el-icon>启用任务
      </el-button>
    </div>

    <!-- Running Tasks Banner -->
    <transition name="banner-slide">
      <div v-if="hasRunningTasks" class="running-banner">
        <div class="banner-header">
          <div class="banner-title">
            <el-icon class="is-loading banner-icon"><Loading /></el-icon>
            <span>{{ runningTasks.size }} 个任务执行中</span>
          </div>
        </div>
        <div class="banner-tasks">
          <div v-for="[taskId, task] in runningTasks" :key="taskId" class="banner-task-item">
            <span class="banner-task-name">{{ task.name }}</span>
            <span class="banner-task-type">
              <el-tag size="small" type="info">{{ task.task_type }}</el-tag>
            </span>
            <span class="banner-task-elapsed">{{ task.elapsed }}s</span>
          </div>
        </div>
        <el-progress :percentage="100" :show-text="false" :indeterminate="true" :stroke-width="4" />
      </div>
    </transition>

    <el-card v-loading="loading">
      <el-table :data="tasks" stripe border>
        <el-table-column prop="name" label="任务名称" min-width="150" />
        <el-table-column prop="task_type" label="任务类型" width="120" />
        <el-table-column prop="command" label="命令" width="120" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="最后执行时间" width="180">
          <template #default="{ row }">
            <span v-if="row.last_run_at">{{ formatTime(row.last_run_at) }}</span>
            <span v-else style="color: #909399">未执行</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :disabled="runningTasks.has(row.id)"
              @click="executeTaskDirect(row)"
            >
              {{ runningTasks.has(row.id) ? '执行中...' : '执行' }}
            </el-button>
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Execution Logs -->
    <el-card class="log-card" v-loading="logsLoading">
      <template #header>
        <div class="log-card-header">
          <span>执行日志</span>
          <div class="log-filter">
            <el-select v-model="logFilterTaskName" placeholder="全部任务" clearable style="width: 200px" @change="fetchLogs(1)">
              <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.task_type" />
            </el-select>
            <el-button size="small" @click="fetchLogs(logsCurrentPage)" style="margin-left: 8px">
              <el-icon><Refresh /></el-icon>刷新
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="logs" stripe border>
        <el-table-column prop="task_name" label="任务名称" width="150" />
        <el-table-column prop="task_type" label="任务类型" width="120" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_seconds" label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration_seconds != null ? row.duration_seconds.toFixed(2) + 's' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="记录数" width="180">
          <template #default="{ row }">
            <span>处理 {{ row.records_processed }}</span>
            <span style="color: #67c23a; margin-left: 4px">+{{ row.records_inserted }}</span>
            <span style="color: #409eff; margin-left: 4px">~{{ row.records_updated }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_type" label="触发方式" width="100">
          <template #default="{ row }">
            {{ row.trigger_type === 'manual' ? '手动' : '定时' }}
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="openLogDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="log-pagination">
        <el-pagination
          v-model:current-page="logsCurrentPage"
          :page-size="logsPageSize"
          :total="logsTotal"
          layout="total, prev, pager, next"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>

    <!-- Log Detail Dialog -->
    <el-dialog
      v-model="logDetailVisible"
      title="执行日志详情"
      width="700px"
    >
      <div v-if="currentLog" class="log-detail">
        <div class="log-detail-row">
          <strong>任务名称：</strong>{{ currentLog.task_name }}
        </div>
        <div class="log-detail-row">
          <strong>任务类型：</strong>{{ currentLog.task_type }}
        </div>
        <div class="log-detail-row">
          <strong>状态：</strong>
          <el-tag :type="statusTagType(currentLog.status)">{{ statusLabel(currentLog.status) }}</el-tag>
        </div>
        <div class="log-detail-row">
          <strong>触发方式：</strong>{{ currentLog.trigger_type === 'manual' ? '手动' : '定时' }}
          <span v-if="currentLog.triggered_by"> ({{ currentLog.triggered_by }})</span>
        </div>
        <div class="log-detail-row">
          <strong>开始时间：</strong>{{ formatTime(currentLog.started_at) }}
        </div>
        <div class="log-detail-row">
          <strong>完成时间：</strong>{{ currentLog.completed_at ? formatTime(currentLog.completed_at) : '-' }}
        </div>
        <div class="log-detail-row">
          <strong>耗时：</strong>{{ currentLog.duration_seconds != null ? currentLog.duration_seconds.toFixed(2) + 's' : '-' }}
        </div>
        <div class="log-detail-row">
          <strong>记录数：</strong>处理 {{ currentLog.records_processed }}，新增 {{ currentLog.records_inserted }}，更新 {{ currentLog.records_updated }}
        </div>
        <div class="log-detail-row">
          <strong>重试次数：</strong>{{ currentLog.retry_count }}
        </div>
        <div v-if="currentLog.error_message" class="result-output error">
          <div class="output-label">错误信息：</div>
          <pre>{{ currentLog.error_message }}</pre>
        </div>
        <div v-if="currentLog.stack_trace" class="result-output error">
          <div class="output-label">堆栈跟踪：</div>
          <pre>{{ currentLog.stack_trace }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="logDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑同步任务' : '新增同步任务'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务名称" required>
          <el-input v-model="form.name" placeholder="例如：同步交易日历" />
        </el-form-item>
        <el-form-item label="任务类型" required>
          <el-select
            v-model="form.task_type"
            placeholder="选择任务类型"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="t in availableTypes"
              :key="t.task_type"
              :label="`${t.task_type} (${t.display_name})`"
              :value="t.task_type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="命令">
          <el-input v-model="form.command" placeholder="默认：stock-sync" />
        </el-form-item>
        <el-form-item label="默认参数">
          <div class="params-form">
            <div v-for="(param, index) in paramList" :key="index" class="param-row">
              <el-input v-model="param.key" placeholder="参数名" style="width: 150px" />
              <el-input v-model="param.value" placeholder="参数值" style="width: 200px; margin-left: 8px" />
              <el-button type="danger" :icon="Delete" circle size="small" style="margin-left: 8px" @click="removeParam(index)" />
            </div>
            <el-button type="primary" size="small" @click="addParam">+ 添加参数</el-button>
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="任务描述" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- Enable Tasks Dialog -->
    <el-dialog
      v-model="enableDialogVisible"
      title="启用任务"
      width="820px"
      class="enable-dialog"
    >
      <div class="enable-dialog-toolbar">
        <el-input
          v-model="availableFilter"
          placeholder="搜索命令..."
          clearable
          :prefix-icon="Search"
          style="width: 260px"
        />
        <span class="enable-dialog-count">
          共 {{ sortedAvailableTypes.length }} 个命令
          <el-tag size="small" type="info" style="margin-left: 8px">未启用 {{ disabledCount }}</el-tag>
          <el-tag size="small" type="success" style="margin-left: 4px">已启用 {{ enabledCount }}</el-tag>
        </span>
      </div>
      <div class="commands-grid enable-grid" v-loading="availableLoading">
        <div
          v-for="cmd in sortedAvailableTypes"
          :key="cmd.task_type"
          class="command-item"
          :class="{ disabled: !cmd.enabled }"
          @click="quickAddCommand(cmd)"
        >
          <div class="command-item-header">
            <span class="command-task-type">{{ cmd.task_type }}</span>
            <el-tag size="small" :type="cmd.enabled ? 'success' : 'info'">
              {{ cmd.enabled ? '已启用' : '未启用' }}
            </el-tag>
          </div>
          <div class="command-display-name">{{ cmd.display_name }}</div>
          <div class="command-schedule">
            <el-icon><Clock /></el-icon>
            <span>{{ cmd.schedule }}</span>
          </div>
        </div>
        <div v-if="sortedAvailableTypes.length === 0 && !availableLoading" class="no-results">
          没有匹配的命令
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Loading, Refresh, Search, Clock } from '@element-plus/icons-vue'
import { syncTaskApi } from '@/api'

const loading = ref(false)
const tasks = ref([])

// Available sync task types from 'stock-sync ls'
const availableTypes = ref([])
const availableLoading = ref(false)
const availableFilter = ref('')

const enableDialogVisible = ref(false)

const filteredAvailableTypes = computed(() => {
  if (!availableFilter.value) return availableTypes.value
  const q = availableFilter.value.toLowerCase()
  return availableTypes.value.filter(
    t =>
      t.task_type.toLowerCase().includes(q) ||
      (t.display_name || '').toLowerCase().includes(q)
  )
})

// Sort: 未启用 (disabled) first, 已启用 (enabled) last
const sortedAvailableTypes = computed(() => {
  return [...filteredAvailableTypes.value].sort((a, b) => {
    if (a.enabled === b.enabled) return 0
    return a.enabled ? 1 : -1
  })
})

const enabledCount = computed(() => sortedAvailableTypes.value.filter(t => t.enabled).length)
const disabledCount = computed(() => sortedAvailableTypes.value.filter(t => !t.enabled).length)

const formatTime = (isoStr) => {
  const d = new Date(isoStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)

const defaultForm = {
  name: '',
  command: 'stock-sync',
  task_type: '',
  params: {},
  description: '',
  sort_order: 0,
  is_active: true
}

const form = reactive({ ...defaultForm })
const paramList = ref([])

// Running tasks tracking (concurrent multi-task support)
const runningTasks = reactive(new Map())
let bannerClearTimer = null

const hasRunningTasks = computed(() => runningTasks.size > 0)

const logsLoading = ref(false)
const logs = ref([])
const logsTotal = ref(0)
const logsCurrentPage = ref(1)
const logsPageSize = ref(10)
const logFilterTaskName = ref(null)
const logDetailVisible = ref(false)
const currentLog = ref(null)

const statusTagType = (status) => {
  const map = { SUCCESS: 'success', FAILED: 'danger', RUNNING: 'warning' }
  return map[status] || 'info'
}

const statusLabel = (status) => {
  const map = { SUCCESS: '成功', FAILED: '失败', RUNNING: '运行中' }
  return map[status] || status
}

const fetchLogs = async (page = 1) => {
  logsLoading.value = true
  try {
    const params = { page, page_size: logsPageSize.value }
    if (logFilterTaskName.value) params.task_name = logFilterTaskName.value
    const res = await syncTaskApi.getLogs(params)
    if (res.success) {
      logs.value = res.data.items || []
      logsTotal.value = res.data.total || 0
      logsCurrentPage.value = page
    }
  } catch (err) {
    ElMessage.error('获取执行日志失败')
  } finally {
    logsLoading.value = false
  }
}

const openLogDetail = (row) => {
  currentLog.value = row
  logDetailVisible.value = true
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await syncTaskApi.getAll()
    if (res.success) {
      tasks.value = res.data || []
    } else {
      ElMessage.error(res.error || '获取任务列表失败')
    }
  } catch (err) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const fetchAvailableTypes = async () => {
  availableLoading.value = true
  try {
    const res = await syncTaskApi.getAvailableTypes()
    if (res.success) {
      availableTypes.value = res.data || []
    } else {
      ElMessage.warning(res.error || '获取可用命令列表失败')
    }
  } catch (err) {
    ElMessage.warning('获取可用命令列表失败')
  } finally {
    availableLoading.value = false
  }
}

const quickAddCommand = (cmd) => {
  enableDialogVisible.value = false
  isEdit.value = false
  editingId.value = null
  Object.assign(form, {
    ...defaultForm,
    name: cmd.display_name || cmd.task_type,
    task_type: cmd.task_type,
    description: cmd.display_name || ''
  })
  paramList.value = []
  dialogVisible.value = true
}

const openEnableDialog = () => {
  enableDialogVisible.value = true
  fetchAvailableTypes()
}

const openCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, defaultForm)
  paramList.value = []
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    command: row.command || 'stock-sync',
    task_type: row.task_type,
    params: row.params || {},
    description: row.description || '',
    sort_order: row.sort_order || 0,
    is_active: row.is_active
  })
  paramList.value = Object.entries(row.params || {}).map(([k, v]) => ({ key: k, value: v }))
  dialogVisible.value = true
}

const addParam = () => {
  paramList.value.push({ key: '', value: '' })
}

const removeParam = (index) => {
  paramList.value.splice(index, 1)
}

const submitForm = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请输入任务名称')
    return
  }
  if (!form.task_type) {
    ElMessage.warning('请选择任务类型')
    return
  }

  const params = {}
  paramList.value.forEach(p => {
    if (p.key.trim()) {
      const val = p.value
      params[p.key.trim()] = typeof val === 'string' ? val.trim() : val
    }
  })

  const payload = {
    ...form,
    params
  }

  try {
    if (isEdit.value) {
      const res = await syncTaskApi.update(editingId.value, payload)
      if (res.success) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        fetchTasks()
      } else {
        ElMessage.error(res.error || '更新失败')
      }
    } else {
      const res = await syncTaskApi.create(payload)
      if (res.success) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        fetchTasks()
      } else {
        ElMessage.error(res.error || '创建失败')
      }
    }
  } catch (err) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除任务 "${row.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    const res = await syncTaskApi.delete(row.id)
    if (res.success) {
      ElMessage.success('删除成功')
      fetchTasks()
    } else {
      ElMessage.error(res.error || '删除失败')
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// Direct task execution (no dialog)
const executeTaskDirect = async (row) => {
  if (runningTasks.has(row.id)) return

  const taskState = reactive({
    id: row.id,
    name: row.name,
    task_type: row.task_type,
    startTime: Date.now(),
    timerInterval: null,
    elapsed: 0
  })

  taskState.timerInterval = setInterval(() => {
    taskState.elapsed = Math.floor((Date.now() - taskState.startTime) / 1000)
  }, 1000)

  runningTasks.set(row.id, taskState)

  // Clear banner dismiss timer if one was pending
  if (bannerClearTimer) {
    clearTimeout(bannerClearTimer)
    bannerClearTimer = null
  }

  try {
    const res = await syncTaskApi.execute(row.id, {})
    if (res.success) {
      ElMessage.success(`任务 "${row.name}" 执行成功 (耗时 ${taskState.elapsed} 秒)`)
    } else {
      ElMessage.error(res.error || `任务 "${row.name}" 执行失败`)
    }
  } catch (err) {
    ElMessage.error(`任务 "${row.name}" 执行失败`)
  } finally {
    clearInterval(taskState.timerInterval)
    runningTasks.delete(row.id)
    fetchLogs(logsCurrentPage.value)

    // Auto-dismiss banner 3 seconds after ALL tasks complete
    if (runningTasks.size === 0) {
      bannerClearTimer = setTimeout(() => {
        bannerClearTimer = null
      }, 3000)
    }
  }
}

onMounted(() => {
  fetchTasks()
  fetchLogs(1)
  fetchAvailableTypes()
})

onUnmounted(() => {
  // Clean up all running task timers
  for (const [, task] of runningTasks) {
    clearInterval(task.timerInterval)
  }
  runningTasks.clear()
  if (bannerClearTimer) {
    clearTimeout(bannerClearTimer)
    bannerClearTimer = null
  }
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
  color: #303133;
  font-size: 24px;
}

/* Running Tasks Banner */
.running-banner {
  margin-bottom: 20px;
  padding: 16px 20px 12px;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f9eb 100%);
  border: 1px solid #b3d8ff;
  border-radius: 8px;
  overflow: hidden;
}
.banner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.banner-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #409eff;
}
.banner-icon {
  font-size: 18px;
}
.banner-tasks {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.banner-task-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: #ffffff;
  border-radius: 4px;
  border: 1px solid #d9ecff;
  font-size: 13px;
  color: #606266;
}
.banner-task-name {
  font-weight: 500;
  color: #303133;
}
.banner-task-elapsed {
  font-variant-numeric: tabular-nums;
  color: #409eff;
  font-weight: 500;
  min-width: 30px;
  text-align: right;
}

/* Banner slide transition */
.banner-slide-enter-active,
.banner-slide-leave-active {
  transition: all 0.3s ease;
  max-height: 200px;
  opacity: 1;
}
.banner-slide-enter-from,
.banner-slide-leave-to {
  max-height: 0;
  opacity: 0;
  margin-bottom: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.log-card {
  margin-top: 20px;
}

/* Available Commands Card */
.available-commands-card {
  margin-top: 20px;
}
.commands-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  min-height: 60px;
}
.enable-grid {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 4px;
}
.enable-dialog-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.enable-dialog-count {
  font-size: 13px;
  color: #606266;
  display: inline-flex;
  align-items: center;
}
.command-item {
  padding: 12px 14px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fafafa;
}
.command-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}
.command-item.disabled {
  opacity: 0.5;
}
.command-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.command-task-type {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.command-display-name {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}
.command-schedule {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  font-variant-numeric: tabular-nums;
}
.command-schedule .el-icon {
  font-size: 12px;
}
.no-results {
  grid-column: 1 / -1;
  text-align: center;
  color: #909399;
  padding: 24px 0;
  font-size: 14px;
}
.log-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.log-card-header span {
  font-size: 16px;
  font-weight: 600;
}
.log-filter {
  display: flex;
  align-items: center;
}
.log-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.log-detail-row {
  margin-bottom: 8px;
}
.params-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.param-row {
  display: flex;
  align-items: center;
}
.result-output.error pre {
  background-color: #fef0f0;
  color: #f56c6c;
}
.output-label {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  color: #606266;
}
.result-output pre {
  margin: 0;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
