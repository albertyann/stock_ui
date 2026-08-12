<template>
  <!-- 审计意见 -->
  <el-card v-if="auditList.length > 0" class="audit-card mt-20">
    <template #header>
      <div class="card-header">
        <span>审计意见</span>
      </div>
    </template>
    <div class="audit-list">
      <div v-for="item in auditList" :key="item.end_date" class="audit-item">
        <div class="audit-item__header">
          <span class="audit-item__period">{{ formatEndDate(item.end_date) }}</span>
          <el-tag
            size="small"
            :type="getAuditTagType(item.audit_result)"
            effect="plain"
          >
            {{ item.audit_result || '-' }}
          </el-tag>
        </div>
        <div class="audit-item__agency" v-if="item.audit_agency">
          {{ item.audit_agency }}
        </div>
      </div>
    </div>
  </el-card>

  <!-- 季度业绩 -->
  <el-card class="mt-20 fina-indicator-card" v-loading="finaIndicatorLoading">
    <template #header>
      <div class="card-header">
        <span>季度业绩</span>
        <span class="signal-count" v-if="finaIndicatorList.length > 0">{{ finaIndicatorList.length }}期</span>
      </div>
    </template>

    <div v-if="finaIndicatorList.length === 0" class="empty-signals">
      <el-empty description="暂无业绩数据" :image-size="60" />
    </div>

    <div v-else class="fina-table">
      <div class="fina-row fina-header">
        <div class="fina-cell">报告期</div>
        <div class="fina-cell">扣非EPS</div>
        <div class="fina-cell">扣非同比</div>
        <div class="fina-cell">营收同比</div>
        <div class="fina-cell">ROE</div>
      </div>
      <div
        v-for="(item, idx) in finaIndicatorList"
        :key="item.end_date"
        class="fina-row"
        :class="{ 'fina-row-loss': isLoss(item) }"
      >
        <div class="fina-cell fina-cell-period">
          {{ formatEndDate(item.end_date) }}
        </div>
        <div class="fina-cell">
          {{ item.dt_eps != null ? item.dt_eps.toFixed(2) : '-' }}
        </div>
        <div class="fina-cell">
          <span :class="getYoyClass(item.dt_netprofit_yoy)">
            {{ formatYoy(item.dt_netprofit_yoy) }}
          </span>
          <el-tag
            v-if="getProfitTag(item, idx)"
            :type="getProfitTag(item, idx).type"
            size="small"
            effect="plain"
            class="fina-tag"
          >
            {{ getProfitTag(item, idx).label }}
          </el-tag>
        </div>
        <div class="fina-cell">
          <span :class="getYoyClass(item.or_yoy)">
            {{ formatYoy(item.or_yoy) }}
          </span>
        </div>
        <div class="fina-cell">
          {{ item.roe != null ? item.roe.toFixed(2) + '%' : '-' }}
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { basicDataApi } from '@/api'
import { formatChange as formatYoy } from '@/utils/stock'

const props = defineProps({
  tsCode: {
    type: String,
    required: true
  }
})

const auditList = ref([])

// 季度业绩
const finaIndicatorList = ref([])
const finaIndicatorLoading = ref(false)

const loadAudit = async () => {
  try {
    const response = await basicDataApi.getFinaAudit(props.tsCode, 5)
    if (response.success) {
      auditList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load audit:', error)
  }
}

// 加载季度业绩
const loadFinaIndicator = async () => {
  finaIndicatorLoading.value = true
  try {
    const response = await basicDataApi.getFinaIndicator(props.tsCode, 8)
    if (response.success) {
      finaIndicatorList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load fina indicator:', error)
  } finally {
    finaIndicatorLoading.value = false
  }
}

// 同比着色 (红涨绿跌, 与项目惯例一致)
const getYoyClass = (val) => {
  if (val == null) return 'muted'
  return val > 0 ? 'up' : val < 0 ? 'down' : 'muted'
}

// 亏损判断 (扣非 EPS < 0 视为亏损, 整行高亮)
const isLoss = (item) => {
  return item.dt_eps != null && item.dt_eps < 0
}

// 盈利趋势 tag (列表按 end_date DESC, idx+1 为上一报告期)
const getProfitTag = (item, idx) => {
  if (item.dt_netprofit_yoy == null) return null
  // 真实亏损
  if (item.dt_eps != null && item.dt_eps < 0) {
    return { type: 'danger', label: '亏损' }
  }

  const prev = finaIndicatorList.value[idx + 1]
  if (!prev || prev.dt_netprofit_yoy == null) {
    if (item.dt_netprofit_yoy > 0) return { type: 'success', label: '增长' }
    if (item.dt_netprofit_yoy < 0) return { type: 'warning', label: '下滑' }
    return null
  }

  const cur = item.dt_netprofit_yoy
  const pre = prev.dt_netprofit_yoy
  // 反转
  if (cur > 0 && pre < 0) return { type: 'success', label: '扭亏' }
  if (cur < 0 && pre > 0) return { type: 'danger', label: '转亏' }
  // 同向变化
  if (cur > pre) return { type: 'success', label: '加速' }
  if (cur < pre) return { type: 'warning', label: '放缓' }
  return null
}

const formatEndDate = (dateStr) => {
  if (!dateStr) return '-'
  // end_date like "2024-12-31" -> "2024年报"
  const parts = dateStr.split('-')
  const year = parts[0]
  const month = parseInt(parts[1], 10)
  if (month === 12) return `${year}年报`
  if (month === 9) return `${year}三季报`
  if (month === 6) return `${year}中报`
  if (month === 3) return `${year}一季报`
  return dateStr
}

const getAuditTagType = (result) => {
  if (!result) return 'info'
  if (result.includes('标准无保留意见') || result.includes('无保留意见')) return 'success'
  if (result.includes('保留意见')) return 'warning'
  if (result.includes('否定意见') || result.includes('无法表示意见')) return 'danger'
  return 'info'
}

onMounted(() => {
  loadAudit()
  loadFinaIndicator()
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

.signal-count {
  font-size: 12px;
  color: var(--text-muted);
}

.empty-signals {
  padding: 20px 0;
}

/* 审计意见 */
.audit-card {
  margin-bottom: 20px;
}

.audit-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.audit-item {
  padding: 8px 10px;
  background-color: var(--bg-input);
  border-radius: 4px;
}

.audit-item__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.audit-item__period {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.audit-item__agency {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  line-height: 1.4;
}

/* 季度业绩卡片 */
.fina-indicator-card :deep(.el-card__body) {
  padding: 4px 12px;
}

.fina-table {
  font-size: 12px;
}

.fina-row {
  display: grid;
  grid-template-columns: 1.2fr 0.9fr 1.5fr 1.1fr 0.9fr;
  gap: 6px;
  padding: 9px 4px;
  border-bottom: 1px solid var(--border-subtle);
  align-items: center;
}

.fina-row:last-child {
  border-bottom: none;
}

.fina-header {
  font-weight: 600;
  color: var(--text-muted);
  background-color: var(--bg-input);
  border-bottom: 1px solid var(--border-subtle);
}

.fina-cell {
  text-align: right;
  white-space: nowrap;
}

.fina-cell-period {
  text-align: left;
  font-weight: 500;
  color: var(--text-primary);
}

.fina-row-loss {
  background-color: var(--bg-input);
}

.fina-tag {
  margin-left: 4px;
  transform: scale(0.85);
  transform-origin: left center;
  vertical-align: middle;
}

.fina-table .up {
  color: var(--stock-up);
  font-weight: 600;
}

.fina-table .down {
  color: var(--stock-down);
  font-weight: 600;
}

.fina-table .muted {
  color: var(--text-muted);
}
</style>
