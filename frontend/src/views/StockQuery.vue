<template>
  <div class="stock-query">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>股票价格查询</span>
        </div>
      </template>

      <el-form :inline="true" @submit.prevent="handleQuery">
        <el-form-item label="股票代码">
          <el-input
            v-model="tsCodesInput"
            type="textarea"
            :rows="3"
            placeholder="输入股票代码，支持逗号或换行分隔&#10;例如: 600000.SH, 000001.SZ&#10;或: 600000&#10;     000001"
            style="width: 400px"
          />
        </el-form-item>
        <el-form-item label="查询日期">
          <el-date-picker
            v-model="queryDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleQuery">
            查询
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="queryResult" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>查询结果</span>
          <div class="trading-dates" v-if="tradingDates">
            <el-tag size="small" type="info">T日: {{ tradingDates['T+0'] }}</el-tag>
            <el-tag size="small">T+1: {{ tradingDates['T+1'] }}</el-tag>
            <el-tag size="small">T+3: {{ tradingDates['T+3'] }}</el-tag>
            <el-tag size="small">T+7: {{ tradingDates['T+7'] }}</el-tag>
            <el-tag size="small">T+30: {{ tradingDates['T+30'] }}</el-tag>
          </div>
        </div>
      </template>

      <el-table
        :data="queryResult"
        style="width: 100%"
        stripe
        border
        :row-class-name="getRowClassName"
        @row-click="handleRowClick"
      >
        <el-table-column label="股票代码" width="130" fixed>
          <template #default="{ row }">
            <a
              :href="getXueqiuUrl(row.ts_code)"
              target="_blank"
              class="stock-link"
              @click.stop="selectRow(row)"
            >
              {{ row.ts_code }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="100" fixed />
        <el-table-column prop="industry" label="板块" width="120" />

        <el-table-column label="T日收盘" width="110" align="right">
          <template #default="{ row }">
            {{ formatPrice(row['close_T+0']) }}
          </template>
        </el-table-column>

        <el-table-column label="T+1 收盘" width="110" align="right">
          <template #default="{ row }">
            {{ formatPrice(row['close_T+1']) }}
          </template>
        </el-table-column>
        <el-table-column label="T+1 涨幅" width="110" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row['change_T+1'])">
              {{ formatPct(row['change_T+1']) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="T+3 收盘" width="110" align="right">
          <template #default="{ row }">
            {{ formatPrice(row['close_T+3']) }}
          </template>
        </el-table-column>
        <el-table-column label="T+3 涨幅" width="110" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row['change_T+3'])">
              {{ formatPct(row['change_T+3']) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="T+7 收盘" width="110" align="right">
          <template #default="{ row }">
            {{ formatPrice(row['close_T+7']) }}
          </template>
        </el-table-column>
        <el-table-column label="T+7 涨幅" width="110" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row['change_T+7'])">
              {{ formatPct(row['change_T+7']) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="T+30 收盘" width="110" align="right">
          <template #default="{ row }">
            {{ formatPrice(row['close_T+30']) }}
          </template>
        </el-table-column>
        <el-table-column label="T+30 涨幅" width="110" align="right">
          <template #default="{ row }">
            <span :class="getChangeClass(row['change_T+30'])">
              {{ formatPct(row['change_T+30']) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click.stop="openFollowDialog(row)"
            >
              关注
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click.stop="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="followDialogVisible"
      title="关注股票"
      width="450px"
      :close-on-click-modal="false"
    >
      <div v-if="currentFollowStock" class="follow-dialog-content">
        <div class="stock-basic-info">
          <h4>股票信息</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="股票代码">
              {{ currentFollowStock.ts_code }}
            </el-descriptions-item>
            <el-descriptions-item label="名称">
              {{ currentFollowStock.name }}
            </el-descriptions-item>
            <el-descriptions-item label="板块">
              {{ currentFollowStock.industry || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="当前价格">
              ¥{{ formatPrice(currentFollowStock['close_T+0']) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="follow-form">
          <h4>关注设置</h4>
          <el-form :model="followForm" label-width="100px">
            <el-form-item label="关注原因">
              <el-select
                v-model="followForm.watch_reason"
                placeholder="请选择关注原因"
                style="width: 100%"
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
                v-model="followForm.watch_date"
                type="date"
                placeholder="选择关注日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disabledDate"
                style="width: 100%"
              />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <template #footer>
        <el-button @click="followDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="followLoading"
          @click="confirmFollow"
        >
          确认关注
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { realtimeApi, watchlistApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const tsCodesInput = ref('')
const queryDate = ref('')
const loading = ref(false)
const queryResult = ref(null)
const tradingDates = ref(null)
const selectedRow = ref(null)

const followDialogVisible = ref(false)
const followLoading = ref(false)
const currentFollowStock = ref(null)
const followForm = ref({
  watch_reason: '',
  watch_date: ''
})
const watchReasons = ref([])

const getTodayDate = () => {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const handleQuery = async () => {
  const codes = tsCodesInput.value
    .split(/[,，\n\t\s]+/)
    .map(c => c.trim())
    .filter(c => c)

  if (!codes.length) {
    ElMessage.warning('请输入至少一个股票代码')
    return
  }

  if (!queryDate.value) {
    ElMessage.warning('请选择查询日期')
    return
  }

  loading.value = true
  try {
    const result = await realtimeApi.queryByDate(codes, queryDate.value)
    queryResult.value = result.data || []
    tradingDates.value = result.trading_dates || null

    if (!queryResult.value.length) {
      ElMessage.info('未查询到数据')
    }
  } catch (error) {
    console.error('Query failed:', error)
    ElMessage.error('查询失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const formatPrice = (price) => {
  if (price === null || price === undefined) return '-'
  return Number(price).toFixed(2)
}

const formatPct = (pct) => {
  if (pct === null || pct === undefined) return '-'
  const val = Number(pct)
  return (val > 0 ? '+' : '') + val.toFixed(2) + '%'
}

const getChangeClass = (val) => {
  if (val === null || val === undefined) return ''
  return val > 0 ? 'up' : val < 0 ? 'down' : ''
}

const getXueqiuUrl = (tsCode) => {
  // ts_code 格式: 002342.SZ → 雪球格式: SZ002342
  const [code, exchange] = tsCode.split('.')
  return `https://xueqiu.com/S/${exchange}${code}`
}

const selectRow = (row) => {
  selectedRow.value = row
}

const handleRowClick = (row) => {
  selectedRow.value = row
}

const getRowClassName = ({ row }) => {
  if (selectedRow.value && row.ts_code === selectedRow.value.ts_code) {
    return 'selected-row'
  }
  return ''
}

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

const openFollowDialog = async (row) => {
  currentFollowStock.value = row
  followForm.value = {
    watch_reason: '',
    watch_date: getTodayDate()
  }
  await loadWatchReasons()
  followDialogVisible.value = true
}

const confirmFollow = async () => {
  if (!followForm.value.watch_reason) {
    ElMessage.warning('请选择关注原因')
    return
  }

  followLoading.value = true
  try {
    await watchlistApi.addStock(8, {
      ts_code: currentFollowStock.value.ts_code,
      watch_reason: followForm.value.watch_reason,
      watch_date: followForm.value.watch_date
    })
    ElMessage.success(`已将 ${currentFollowStock.value.name} (${currentFollowStock.value.ts_code}) 添加到关注列表`)
    followDialogVisible.value = false
  } catch (error) {
    console.error('Follow failed:', error)
    ElMessage.error('关注失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    followLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.name} (${row.ts_code}) 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    queryResult.value = queryResult.value.filter(
      (item) => item.ts_code !== row.ts_code
    )

    if (selectedRow.value?.ts_code === row.ts_code) {
      selectedRow.value = null
    }

    ElMessage.success('已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.stock-query {
  padding: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trading-dates {
  display: flex;
  gap: 8px;
}

.up {
  color: #f56c6c;
  font-weight: 500;
}

.down {
  color: #67c23a;
  font-weight: 500;
}

.stock-link {
  color: #409eff;
  text-decoration: none;
}

.stock-link:hover {
  text-decoration: underline;
}
:deep(.selected-row) {
  background-color: #e6f7ff !important;
}

:deep(.selected-row:hover > td) {
  background-color: #e6f7ff !important;
}

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
</style>
