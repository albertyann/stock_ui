<template>
  <div class="page-container">
    <div class="page-header">
      <h2>同步任务管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>新增任务
      </el-button>
    </div>

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
            <el-button type="primary" size="small" @click="openExecuteDialog(row)">执行</el-button>
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
          <el-select v-model="form.task_type" placeholder="选择任务类型" style="width: 100%">
            <el-option label="trade_cal (交易日历)" value="trade_cal" />
            <el-option label="daily_data (日线数据)" value="daily_data" />
            <el-option label="rt_k (实时日线数据)" value="rt_k" />
            <el-option label="weekly_data (周线数据)" value="weekly_data" />
            <el-option label="stock_basic (股票基本信息)" value="stock_basic" />
            <el-option label="moneyflow (资金流动)" value="moneyflow" />
            <el-option label="moneyflow_hsgt (北向资金)" value="moneyflow_hsgt" />
            <el-option label="moneyflow_ind_ths (同花顺行业资金流)" value="moneyflow_ind_ths" />
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

    <!-- Execute Dialog -->
    <el-dialog
      v-model="executeDialogVisible"
      :title="`执行任务：${currentTask?.name || ''}`"
      width="700px"
    >
      <el-form :model="executeForm" label-width="120px">
        <el-form-item label="任务类型">
          <el-tag>{{ currentTask?.task_type }}</el-tag>
        </el-form-item>
        <el-form-item label="执行命令">
          <el-input :model-value="previewCommand" readonly type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="运行参数">
          <div class="params-form">
            <div v-for="(param, index) in executeParamList" :key="index" class="param-row">
              <el-input v-model="param.key" placeholder="参数名" style="width: 150px" />
              <el-input v-model="param.value" placeholder="参数值" style="width: 200px; margin-left: 8px" />
              <el-button type="danger" :icon="Delete" circle size="small" style="margin-left: 8px" @click="removeExecuteParam(index)" />
            </div>
            <el-button type="primary" size="small" @click="addExecuteParam">+ 添加参数</el-button>
          </div>
          <div class="param-tips">
            <p>常用参数：</p>
            <ul>
              <li><code>days</code> - 同步天数（覆盖配置，如 30）</li>
              <li><code>date</code> - 指定日期（格式：YYYY-MM-DD）</li>
              <li><code>start_date</code> / <code>end_date</code> - 日期范围</li>
            </ul>
          </div>
        </el-form-item>
      </el-form>

      <div v-if="executing" class="executing-progress">
        <el-divider />
        <div class="progress-content">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>任务执行中... 已耗时 {{ elapsedTime }} 秒</span>
        </div>
        <el-progress :percentage="100" :status="executing ? '' : 'success'" :show-text="false" :indeterminate="true" />
      </div>

      <div v-if="executeResult" class="execute-result">
        <el-divider />
        <div class="result-header">
          <span>执行结果</span>
          <el-tag :type="executeResult.success ? 'success' : 'danger'">
            {{ executeResult.success ? '成功' : '失败' }}
          </el-tag>
        </div>
        <div v-if="executeResult.command" class="result-command">
          <strong>命令：</strong>{{ executeResult.command }}
        </div>
        <div v-if="executeResult.stdout" class="result-output">
          <div class="output-label">标准输出：</div>
          <pre>{{ executeResult.stdout }}</pre>
        </div>
        <div v-if="executeResult.stderr" class="result-output error">
          <div class="output-label">错误输出：</div>
          <pre>{{ executeResult.stderr }}</pre>
        </div>
        <div v-if="executeResult.error" class="result-output error">
          <div class="output-label">错误信息：</div>
          <pre>{{ executeResult.error }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="executeDialogVisible = false" :disabled="executing">关闭</el-button>
        <el-button type="primary" :loading="executing" @click="runTask">
          {{ executing ? '执行中...' : '立即执行' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Loading, Refresh } from '@element-plus/icons-vue'
import { syncTaskApi } from '@/api'

const loading = ref(false)
const tasks = ref([])

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

const executeDialogVisible = ref(false)
const currentTask = ref(null)
const executing = ref(false)
const executeResult = ref(null)
const executeForm = reactive({ params: {} })
const executeParamList = ref([])
const elapsedTime = ref(0)
let timerInterval = null

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

const previewCommand = computed(() => {
  if (!currentTask.value) return ''
  const parts = [currentTask.value.command || 'stock-sync']
  if (currentTask.value.task_type) {
    parts.push(currentTask.value.task_type)
  }

  const params = {}
  if (currentTask.value.params) {
    Object.assign(params, currentTask.value.params)
  }
  executeParamList.value.forEach(p => {
    if (p.key) params[p.key] = p.value
  })

  Object.entries(params).forEach(([key, value]) => {
    if (value === '' || value === null || value === undefined) return
    if (key === 'date') {
      parts.push('--date')
    } else if (key === 'start_date') {
      parts.push('--start-date')
    } else if (key === 'end_date') {
      parts.push('--end-date')
    } else {
      parts.push(`--${key}`)
    }
    parts.push(String(value))
  })

  return parts.join(' ')
})

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

const openExecuteDialog = (row) => {
  currentTask.value = row
  executeResult.value = null
  executeParamList.value = []
  elapsedTime.value = 0
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  executeDialogVisible.value = true
}

const addExecuteParam = () => {
  executeParamList.value.push({ key: '', value: '' })
}

const removeExecuteParam = (index) => {
  executeParamList.value.splice(index, 1)
}

const runTask = async () => {
  if (!currentTask.value) return

  const params = {}
  executeParamList.value.forEach(p => {
    if (p.key.trim()) {
      const key = p.key.trim()
      let value = p.value.trim()
      if (value === 'true') value = true
      else if (value === 'false') value = false
      else if (/^\d+$/.test(value)) value = Number(value)
      params[key] = value
    }
  })

  executing.value = true
  executeResult.value = null
  elapsedTime.value = 0
  
  timerInterval = setInterval(() => {
    elapsedTime.value++
  }, 1000)
  
  try {
    const res = await syncTaskApi.execute(currentTask.value.id, params)
    executeResult.value = res
    if (res.success) {
      ElMessage.success(`任务执行成功 (耗时 ${elapsedTime.value} 秒)`)
      fetchLogs(logsCurrentPage.value)
    } else {
      ElMessage.error(res.error || '任务执行失败')
    }
  } catch (err) {
    ElMessage.error('任务执行失败')
    executeResult.value = { success: false, error: err.message || '执行失败' }
  } finally {
    clearInterval(timerInterval)
    timerInterval = null
    executing.value = false
  }
}

watch(executeDialogVisible, (newVal) => {
  if (!newVal && timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
})

onMounted(() => {
  fetchTasks()
  fetchLogs(1)
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
.log-card {
  margin-top: 20px;
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
.param-tips {
  margin-top: 12px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}
.param-tips p {
  margin: 0 0 8px 0;
  font-weight: 500;
}
.param-tips ul {
  margin: 0;
  padding-left: 18px;
}
.param-tips li {
  margin-bottom: 4px;
}
.param-tips code {
  background-color: #e4e7ed;
  padding: 1px 4px;
  border-radius: 3px;
  font-family: monospace;
}
.executing-progress {
  margin-top: 10px;
}
.progress-content {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #409eff;
  font-weight: 500;
}
.execute-result {
  margin-top: 10px;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 500;
}
.result-command {
  margin-bottom: 12px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  word-break: break-all;
}
.result-output {
  margin-bottom: 12px;
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
