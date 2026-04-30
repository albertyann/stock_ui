<template>
  <div class="ma-slope">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>均线斜率</span>
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

    <el-card v-if="queryResult.length > 0" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>查询结果</span>
          <el-tag size="small" type="info">共 {{ queryResult.length }} 只股票</el-tag>
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

        <!-- 日线斜率 -->
        <el-table-column label="日线斜率" align="center">
          <el-table-column label="MA5" width="100" align="right">
            <template #default="{ row }">
              <span :class="getSlopeClass(row.daily_ma5_slope)">
                {{ formatSlope(row.daily_ma5_slope) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="MA10" width="100" align="right">
            <template #default="{ row }">
              <span :class="getSlopeClass(row.daily_ma10_slope)">
                {{ formatSlope(row.daily_ma10_slope) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="MA20" width="100" align="right">
            <template #default="{ row }">
              <span :class="getSlopeClass(row.daily_ma20_slope)">
                {{ formatSlope(row.daily_ma20_slope) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="MA30" width="100" align="right">
            <template #default="{ row }">
              <span :class="getSlopeClass(row.daily_ma30_slope)">
                {{ formatSlope(row.daily_ma30_slope) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="MA60" width="100" align="right">
            <template #default="{ row }">
              <span :class="getSlopeClass(row.daily_ma60_slope)">
                {{ formatSlope(row.daily_ma60_slope) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 周线斜率 -->
        <el-table-column label="周线斜率" align="center">
          <el-table-column label="MA5" width="100" align="right">
            <template #default="{ row }">
              <span :class="getSlopeClass(row.weekly_ma5_slope)">
                {{ formatSlope(row.weekly_ma5_slope) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="MA10" width="100" align="right">
            <template #default="{ row }">
              <span :class="getSlopeClass(row.weekly_ma10_slope)">
                {{ formatSlope(row.weekly_ma10_slope) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { realtimeApi } from '@/api'
import { ElMessage } from 'element-plus'

const tsCodesInput = ref('')
const queryDate = ref('')
const loading = ref(false)
const queryResult = ref([])
const selectedRow = ref(null)

const getTodayDate = () => {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const parseTsCodes = (input) => {
  return input
    .split(/[,，\n\t\s]+/)
    .map(c => c.trim())
    .filter(c => c)
}

const normalizeTsCode = (code) => {
  code = code.trim().toUpperCase()
  if (/\.SH$|\.SZ$|\.BJ$/.test(code)) {
    return code
  }
  if (code.startsWith('6')) {
    return `${code}.SH`
  } else if (code.startsWith('0') || code.startsWith('3')) {
    return `${code}.SZ`
  } else if (code.startsWith('4') || code.startsWith('8') || code.startsWith('9')) {
    return `${code}.BJ`
  }
  return `${code}.SZ`
}

const handleQuery = async () => {
  const codes = parseTsCodes(tsCodesInput.value)

  if (!codes.length) {
    ElMessage.warning('请输入至少一个股票代码')
    return
  }

  if (!queryDate.value) {
    ElMessage.warning('请选择查询日期')
    return
  }

  const normalizedCodes = codes.map(normalizeTsCode)

  loading.value = true
  queryResult.value = []

  try {
    // 批量获取日线数据（需要至少 61 天数据来计算 MA60 及前一日的 MA60）
    const dailyRes = await realtimeApi.getBatchKline(normalizedCodes, 'daily', 80)
    // 批量获取周线数据（需要至少 11 周数据来计算 MA10 及前一日的 MA10）
    const weeklyRes = await realtimeApi.getBatchKline(normalizedCodes, 'weekly', 20)

    const dailyKlineData = dailyRes.data?.kline_data || {}
    const weeklyKlineData = weeklyRes.data?.kline_data || {}

    const results = []

    for (const tsCode of normalizedCodes) {
      const dailyData = dailyKlineData[tsCode] || []
      const weeklyData = weeklyKlineData[tsCode] || []

      const dailySlopes = calculateMASlopes(dailyData, queryDate.value, [5, 10, 20, 30, 60], 'daily')
      const weeklySlopes = calculateMASlopes(weeklyData, queryDate.value, [5, 10], 'weekly')

      if (!dailySlopes) {
        continue
      }

      results.push({
        ts_code: tsCode,
        name: dailySlopes.name || tsCode,
        daily_ma5_slope: dailySlopes.ma5,
        daily_ma10_slope: dailySlopes.ma10,
        daily_ma20_slope: dailySlopes.ma20,
        daily_ma30_slope: dailySlopes.ma30,
        daily_ma60_slope: dailySlopes.ma60,
        weekly_ma5_slope: weeklySlopes?.ma5 || null,
        weekly_ma10_slope: weeklySlopes?.ma10 || null,
      })
    }

    queryResult.value = results

    if (!results.length) {
      ElMessage.info('未查询到数据，请检查股票代码和日期')
    }
  } catch (error) {
    console.error('Query failed:', error)
    ElMessage.error('查询失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

/**
 * 计算均线斜率
 * @param {Array} klineData - K线数据，按日期升序排列
 * @param {string} queryDate - 查询日期
 * @param {Array} maPeriods - MA周期列表
 * @param {string} period - 周期类型
 */
const calculateMASlopes = (klineData, queryDate, maPeriods, period) => {
  if (!klineData || klineData.length === 0) {
    return null
  }

  // 找到查询日期对应的索引
  let targetIndex = -1
  for (let i = 0; i < klineData.length; i++) {
    if (klineData[i].date === queryDate) {
      targetIndex = i
      break
    }
  }

  // 如果找不到精确日期，找最近的前一个交易日
  if (targetIndex === -1) {
    for (let i = klineData.length - 1; i >= 0; i--) {
      if (klineData[i].date < queryDate) {
        targetIndex = i
        break
      }
    }
  }

  if (targetIndex === -1 || targetIndex < 1) {
    return null
  }

  const maxPeriod = Math.max(...maPeriods)
  if (targetIndex < maxPeriod) {
    return null
  }

  const result = { name: klineData[targetIndex].name || '' }

  for (const maPeriod of maPeriods) {
    // 计算查询日期的 MA
    const currentMA = calculateMA(klineData, targetIndex, maPeriod)
    // 计算前一期的 MA
    const prevMA = calculateMA(klineData, targetIndex - 1, maPeriod)

    if (currentMA !== null && prevMA !== null && prevMA !== 0) {
      // 斜率 = (当前MA - 前一期MA) / 前一期MA * 100
      result[`ma${maPeriod}`] = ((currentMA - prevMA) / prevMA) * 100
    } else {
      result[`ma${maPeriod}`] = null
    }
  }

  return result
}

/**
 * 计算移动平均值
 * @param {Array} data - K线数据
 * @param {number} endIndex - 结束索引（包含）
 * @param {number} period - 周期
 */
const calculateMA = (data, endIndex, period) => {
  if (endIndex < period - 1) {
    return null
  }

  let sum = 0
  for (let i = endIndex - period + 1; i <= endIndex; i++) {
    sum += data[i].close
  }

  return sum / period
}

const formatSlope = (slope) => {
  if (slope === null || slope === undefined) return '-'
  const val = Number(slope)
  return (val > 0 ? '+' : '') + val.toFixed(2) + '%'
}

const getSlopeClass = (val) => {
  if (val === null || val === undefined) return ''
  return val > 0 ? 'up' : val < 0 ? 'down' : ''
}

const getXueqiuUrl = (tsCode) => {
  return `/stock/${tsCode}`
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
</script>

<style scoped>
.ma-slope {
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
</style>
