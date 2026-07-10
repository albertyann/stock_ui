<template>
  <div class="concept-sectors-page">
    <div class="page-header">
      <div class="header-title">
        <h2>{{ pageTitle }}</h2>
        <el-tag v-if="tradeDate" type="info" size="small" class="date-tag">
          数据日期: {{ tradeDate }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-radio-group v-model="sectorType" size="small" @change="handleTypeChange" style="margin-right: 10px;">
          <el-radio-button label="industry">行业板块</el-radio-button>
          <el-radio-button label="region">地域板块</el-radio-button>
          <el-radio-button label="concept">概念板块</el-radio-button>
        </el-radio-group>
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :disabled="loading"
          @change="handleDateChange"
          style="margin-right: 10px;"
        />
        <el-button type="primary" @click="fetchSectors" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <el-card class="search-card">
      <el-input
        v-model="searchQuery"
        placeholder="搜索板块名称或代码"
        clearable
        :prefix-icon="Search"
        @input="handleSearch"
      />
    </el-card>

    <el-row :gutter="20" class="stats-row" v-if="filteredSectors.length > 0">
      <el-col :xs="12" :sm="6" :md="6" :lg="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ filteredSectors.length }}</div>
          <div class="stat-label">板块总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6">
        <el-card class="stat-card up">
          <div class="stat-value">{{ upCount }}</div>
          <div class="stat-label">上涨板块</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6">
        <el-card class="stat-card down">
          <div class="stat-value">{{ downCount }}</div>
          <div class="stat-label">下跌板块</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ avgChange }}%</div>
          <div class="stat-label">平均涨跌</div>
        </el-card>
      </el-col>
    </el-row>

    <div v-loading="loading" class="sectors-container">
      <el-empty v-if="!loading && filteredSectors.length === 0" description="暂无板块数据" />

      <div v-if="filteredSectors.length > 0" class="sector-grid">
        <el-card
          v-for="sector in filteredSectors"
          :key="sector.code"
          class="sector-card"
          :class="getSectorClass(sector.change_pct)"
          shadow="hover"
          @click="goToSector(sector)"
        >
          <div class="sector-header">
            <div class="sector-info">
              <div class="sector-name">{{ sector.name }}</div>
              <div class="sector-code">{{ sector.code }}</div>
              <el-tag :type="getSectorTagType(sector.type || sectorType)" size="small">
                {{ getSectorTagText(sector.type || sectorType) }}
              </el-tag>
            </div>
            <div class="sector-change" :class="getChangeClass(sector.change_pct)">
              {{ formatChange(sector.change_pct) }}
            </div>
          </div>

          <div class="sector-leading" v-if="sector.leading">
            <div class="leading-label">领涨股</div>
            <div class="leading-stock">
              <span class="leading-name">{{ sector.leading }}</span>
              <span class="leading-pct" :class="getChangeClass(sector.leading_pct)">
                {{ formatChange(sector.leading_pct) }}
              </span>
            </div>
          </div>

          <div class="sector-stats">
            <div class="stat-item">
              <span class="stat-label">涨/跌家数</span>
              <span class="stat-value">
                <span class="up-num">{{ sector.up_num }}</span>
                /
                <span class="down-num">{{ sector.down_num }}</span>
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">换手率</span>
              <span class="stat-value">{{ sector.turnover_rate?.toFixed(2) }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总市值</span>
              <span class="stat-value">{{ formatAmount(sector.total_mv, { symbol: true }) }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { sectorApi } from '@/api'
import { getChangeClass, formatChange, formatAmount } from '@/utils/stock'

const router = useRouter()
const route = useRoute()

const sectors = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedDate = ref('')
const tradeDate = ref('')
const sectorType = ref('concept')

const filteredSectors = computed(() => {
  let result = sectors.value

  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(s =>
      s.name?.toLowerCase().includes(query) ||
      s.code?.toLowerCase().includes(query)
    )
  }

  return result
})

const upCount = computed(() => filteredSectors.value.filter(s => s.change_pct > 0).length)
const downCount = computed(() => filteredSectors.value.filter(s => s.change_pct < 0).length)
const avgChange = computed(() => {
  if (filteredSectors.value.length === 0) return '0.00'
  const avg = filteredSectors.value.reduce((sum, s) => sum + s.change_pct, 0) / filteredSectors.value.length
  return avg.toFixed(2)
})

const pageTitle = computed(() => {
  const titles = {
    'industry': '行业板块',
    'region': '地域板块',
    'concept': '概念板块'
  }
  return titles[sectorType.value] || '板块列表'
})

const fetchSectors = async () => {
  loading.value = true
  try {
    const response = await sectorApi.getConceptSectors(selectedDate.value, sectorType.value)
    if (response.success) {
      sectors.value = response.data || []
      if (sectors.value.length > 0 && sectors.value[0].trade_date) {
        tradeDate.value = sectors.value[0].trade_date
      }
      const typeNames = {
        'industry': '行业',
        'region': '地域',
        'concept': '概念'
      }
      ElMessage.success(`成功获取 ${sectors.value.length} 个${typeNames[sectorType.value]}板块`)
    } else {
      ElMessage.error(response.error || '获取板块数据失败')
    }
  } catch (error) {
    console.error('Failed to fetch sectors:', error)
    ElMessage.error('获取板块数据失败：' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

const handleDateChange = (date) => {
  if (date) {
    fetchSectors()
  }
}

const handleTypeChange = (type) => {
  sectorType.value = type
  sectors.value = []
  tradeDate.value = ''
  fetchSectors()
}

let searchTimeout = null
const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {}, 300)
}

const goToSector = (sector) => {
  const type = sector.type || sectorType.value
  const date = selectedDate.value || tradeDate.value || ''
  router.push({
    path: '/concept/detail',
    query: {
      code: sector.code,
      sectorType: type,
      sectorName: sector.name,
      tradeDate: date
    }
  })
}

const getSectorClass = (changePct) => {
  if (changePct > 0) return 'sector-up'
  if (changePct < 0) return 'sector-down'
  return 'sector-flat'
}

const getSectorTagType = (type) => {
  const tagTypes = {
    'industry': 'success',
    'region': 'primary',
    'concept': 'warning'
  }
  return tagTypes[type] || 'info'
}

const getSectorTagText = (type) => {
  const tagTexts = {
    'industry': '行业',
    'region': '地域',
    'concept': '概念'
  }
  return tagTexts[type] || '板块'
}

// 同步板块类型到 URL 查询参数
watch(sectorType, (newType) => {
  router.replace({
    query: {
      ...route.query,
      sectorType: newType
    }
  })
})

onMounted(() => {
  // 从 URL 查询参数读取板块类型
  const typeFromQuery = route.query.sectorType
  if (typeFromQuery && ['industry', 'region', 'concept'].includes(typeFromQuery)) {
    sectorType.value = typeFromQuery
  }
  fetchSectors()
})
</script>

<style scoped>
.concept-sectors-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
}

.date-tag {
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.search-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--accent);
  margin-bottom: 5px;
}

.stat-card.up .stat-value {
  color: var(--stock-up);
}

.stat-card.down .stat-value {
  color: var(--stock-down);
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

.sectors-container {
  min-height: 200px;
}

.sector-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.sector-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.sector-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.sector-card.sector-up {
  border-color: var(--stock-up);
}

.sector-card.sector-down {
  border-color: var(--stock-down);
}

.sector-card.sector-flat {
  border-color: var(--border-subtle);
}

.sector-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.sector-info {
  flex: 1;
}

.sector-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.sector-code {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.sector-change {
  font-size: 20px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 6px;
}

.sector-change.up {
  color: var(--stock-up);
  background: rgba(239, 68, 68, 0.12);
}

.sector-change.down {
  color: var(--stock-down);
  background: rgba(34, 197, 94, 0.12);
}

.sector-change.flat {
  color: var(--stock-flat);
  background: rgba(100, 116, 139, 0.12);
}

.sector-leading {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--bg-input);
  border-radius: 6px;
}

.leading-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.leading-stock {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.leading-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.leading-pct {
  font-size: 14px;
  font-weight: 600;
}

.leading-pct.up {
  color: var(--stock-up);
}

.leading-pct.down {
  color: var(--stock-down);
}

.sector-stats {
  display: flex;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}

.stat-item {
  text-align: center;
}

.stat-item .stat-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.stat-item .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.up-num {
  color: var(--stock-up);
}

.down-num {
  color: var(--stock-down);
}

@media (max-width: 768px) {
  .concept-sectors-page {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .sector-grid {
    grid-template-columns: 1fr;
  }
}
</style>
