<template>
  <div class="page-container">
    <div class="page-header">
      <h2>ETF 同步</h2>
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
            <span class="banner-task-elapsed">{{ task.elapsed }}s</span>
          </div>
        </div>
        <el-progress :percentage="100" :show-text="false" :indeterminate="true" :stroke-width="4" />
      </div>
    </transition>

    <!-- ETF Sync Cards -->
    <div class="etf-cards" v-loading="loading">
      <div
        v-for="cmd in etfCommands"
        :key="cmd.task_type"
        class="etf-card"
        :class="{ running: runningTaskByType(cmd.task_type) }"
      >
        <div class="card-body">
          <div class="card-icon">
            <el-icon :size="28"><Coin /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-title">{{ cmd.display_name || cmd.task_type }}</div>
            <div class="card-desc">{{ cmd.description || cmd.task_type }}</div>
            <div class="card-meta">
              <el-tag size="small" :type="taskStatus(cmd).tagType">
                {{ taskStatus(cmd).label }}
              </el-tag>
              <span v-if="taskLastRun(cmd)" class="last-run">
                上次: {{ taskLastRun(cmd) }}
              </span>
            </div>
          </div>
          <div class="card-actions">
            <el-button
              type="primary"
              :loading="runningTaskByType(cmd.task_type)"
              :disabled="runningTaskByType(cmd.task_type)"
              @click="executeSync(cmd)"
            >
              {{ runningTaskByType(cmd.task_type) ? '同步中...' : '执行同步' }}
            </el-button>
          </div>
        </div>
      </div>
      <div v-if="etfCommands.length === 0 && !loading" class="no-commands">
        <el-empty description="暂无可用的 ETF 同步任务" />
      </div>
    </div>

    <!-- Execution Logs -->
    <el-card class="log-card">
      <template #header>
        <div class="log-card-header">
          <span>执行日志</span>
          <div class="log-actions">
            <el-button size="small" @click="fetchLogs(1)">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="logs" stripe border v-loading="logsLoading">
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
        <el-table-column prop="completed_at" label="执行时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.completed_at) }}
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
    <el-dialog v-model="logDetailVisible" title="执行日志详情" width="700px">
      <div v-if="currentLog" class="log-detail">
        <div class="log-detail-row"><strong>任务名称：</strong>{{ currentLog.task_name }}</div>
        <div class="log-detail-row"><strong>任务类型：</strong>{{ currentLog.task_type }}</div>
        <div class="log-detail-row">
          <strong>状态：</strong>
          <el-tag :type="statusTagType(currentLog.status)">{{ statusLabel(currentLog.status) }}</el-tag>
        </div>
        <div class="log-detail-row">
          <strong>触发方式：</strong>{{ currentLog.trigger_type === 'manual' ? '手动' : '定时' }}
          <span v-if="currentLog.triggered_by"> ({{ currentLog.triggered_by }})</span>
        </div>
        <div class="log-detail-row"><strong>开始时间：</strong>{{ formatTime(currentLog.started_at) }}</div>
        <div class="log-detail-row"><strong>完成时间：</strong>{{ currentLog.completed_at ? formatTime(currentLog.completed_at) : '-' }}</div>
        <div class="log-detail-row"><strong>耗时：</strong>{{ currentLog.duration_seconds != null ? currentLog.duration_seconds.toFixed(2) + 's' : '-' }}</div>
        <div class="log-detail-row">
          <strong>记录数：</strong>处理 {{ currentLog.records_processed }}，新增 {{ currentLog.records_inserted }}，更新 {{ currentLog.records_updated }}
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Refresh, Coin } from '@element-plus/icons-vue'
import { syncTaskApi } from '@/api'

// ETF sync task types we care about
const ETF_TASK_TYPES = ['etf_basic', 'etf_daily', 'etf_share_size', 'fund_adj']

const loading = ref(false)
const availableTypes = ref([])
const configuredTasks = ref([])

// Running tasks tracking
const runningTasks = reactive(new Map())
let bannerClearTimer = null

const hasRunningTasks = computed(() => runningTasks.size > 0)

// Compute ETF commands with merged info from available types + configured tasks
const etfCommands = computed(() => {
  return availableTypes.value
    .filter(t => ETF_TASK_TYPES.includes(t.task_type))
    .map(t => {
      const configured = configuredTasks.value.find(ct => ct.task_type === t.task_type)
      return {
        ...t,
        configuredTask: configured || null,
        configured: !!configured
      }
    })
})

const runningTaskByType = (taskType) => {
  for (const [, task] of runningTasks) {
    if (task.task_type === taskType) return true
  }
  return false
}

const taskStatus = (cmd) => {
  if (cmd.configured && cmd.configuredTask.is_active) {
    return { tagType: 'success', label: '已启用' }
  }
  if (cmd.configured) {
    return { tagType: 'warning', label: '已禁用' }
  }
  return { tagType: 'info', label: '未配置' }
}

const taskLastRun = (cmd) => {
  if (!cmd.configuredTask || !cmd.configuredTask.last_run_at) return null
  return formatTime(cmd.configuredTask.last_run_at)
}

// Logs
const logsLoading = ref(false)
const logs = ref([])
const logsTotal = ref(0)
const logsCurrentPage = ref(1)
const logsPageSize = ref(10)
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

const formatTime = (isoStr) => {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const s = d.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false
  })
  return s.replace(/\//g, '-')
}

const fetchLogs = async (page = 1) => {
  logsLoading.value = true
  try {
    const params = { page, page_size: logsPageSize.value }
    const res = await syncTaskApi.getLogs(params)
    if (res.success) {
      logs.value = (res.data.items || []).filter(
        l => ETF_TASK_TYPES.includes(l.task_type)
      )
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

const fetchData = async () => {
  loading.value = true
  try {
    const [typesRes, tasksRes] = await Promise.all([
      syncTaskApi.getAvailableTypes(),
      syncTaskApi.getAll()
    ])
    if (typesRes.success) availableTypes.value = typesRes.data || []
    if (tasksRes.success) configuredTasks.value = tasksRes.data || []
  } catch (err) {
    ElMessage.error('获取ETF同步任务失败')
  } finally {
    loading.value = false
  }
}

const ensureAndExecute = async (cmd) => {
  // If task is already configured, execute directly
  if (cmd.configured && cmd.configuredTask) {
    return cmd.configuredTask.id
  }

  // Create the task first
  const payload = {
    name: cmd.display_name || cmd.task_type,
    command: 'stock-sync',
    task_type: cmd.task_type,
    description: cmd.display_name || '',
    params: {},
    is_active: true
  }

  const res = await syncTaskApi.create(payload)
  if (!res.success) {
    throw new Error(res.error || '创建任务失败')
  }

  // Refresh configured tasks
  const tasksRes = await syncTaskApi.getAll()
  if (tasksRes.success) configuredTasks.value = tasksRes.data || []

  return res.data.id
}

const executeSync = async (cmd) => {
  let taskId
  try {
    taskId = await ensureAndExecute(cmd)
  } catch (err) {
    ElMessage.error(`准备任务失败: ${err.message}`)
    return
  }

  const task = configuredTasks.value.find(t => t.id === taskId)
  if (!task) {
    ElMessage.error('任务未找到')
    return
  }

  // Start tracking
  const taskState = reactive({
    id: task.id,
    name: task.name,
    task_type: task.task_type,
    startTime: Date.now(),
    timerInterval: null,
    elapsed: 0
  })

  taskState.timerInterval = setInterval(() => {
    taskState.elapsed = Math.floor((Date.now() - taskState.startTime) / 1000)
  }, 1000)

  runningTasks.set(task.id, taskState)

  if (bannerClearTimer) {
    clearTimeout(bannerClearTimer)
    bannerClearTimer = null
  }

  try {
    const res = await syncTaskApi.execute(task.id, {})
    if (res.success) {
      ElMessage.success(`"${cmd.display_name || cmd.task_type}" 同步成功 (耗时 ${taskState.elapsed} 秒)`)
    } else {
      ElMessage.error(res.error || `"${cmd.display_name || cmd.task_type}" 同步失败`)
    }
  } catch (err) {
    ElMessage.error(`"${cmd.display_name || cmd.task_type}" 同步失败`)
  } finally {
    clearInterval(taskState.timerInterval)
    runningTasks.delete(task.id)
    fetchLogs(logsCurrentPage.value)
    fetchData() // Refresh task status

    if (runningTasks.size === 0) {
      bannerClearTimer = setTimeout(() => {
        bannerClearTimer = null
      }, 3000)
    }
  }
}

onMounted(() => {
  fetchData()
  fetchLogs(1)
})

onUnmounted(() => {
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
  color: var(--text-primary);
  font-size: 24px;
}

/* Running Tasks Banner */
.running-banner {
  margin-bottom: 20px;
  padding: 16px 20px 12px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 182, 212, 0.08));
  border: 1px solid var(--border-active);
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
  color: var(--accent);
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
  background: var(--bg-card-solid);
  border-radius: 4px;
  border: 1px solid var(--bg-active);
  font-size: 13px;
  color: var(--text-secondary);
}
.banner-task-name {
  font-weight: 500;
  color: var(--text-primary);
}
.banner-task-elapsed {
  font-variant-numeric: tabular-nums;
  color: var(--accent);
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

/* ETF Cards */
.etf-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
  min-height: 100px;
}
.etf-card {
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-card-solid);
  transition: all 0.2s ease;
}
.etf-card:hover {
  border-color: var(--border-active);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
.etf-card.running {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}
.card-body {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}
.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 182, 212, 0.08));
  color: var(--accent);
  flex-shrink: 0;
}
.card-info {
  flex: 1;
  min-width: 0;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.last-run {
  font-size: 12px;
  color: var(--text-muted);
}
.card-actions {
  flex-shrink: 0;
}
.no-commands {
  grid-column: 1 / -1;
}
.log-card {
  margin-top: 0;
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
.log-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.log-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.log-detail-row {
  margin-bottom: 8px;
}
.output-label {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  color: var(--text-secondary);
}
.result-output pre {
  margin: 0;
  padding: 12px;
  background-color: var(--bg-input);
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
.result-output.error pre {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--stock-up);
}
</style>
