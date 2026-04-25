<template>
  <div class="sector-list-page">
    <div class="page-header">
      <h2>板块列表</h2>
      <div class="header-actions">
        <el-radio-group v-model="filterType" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="industry">行业</el-radio-button>
          <el-radio-button label="concept">概念</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="fetchSectors" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索框 -->
    <el-card class="search-card">
      <el-input
        v-model="searchQuery"
        placeholder="搜索板块名称或代码"
        clearable
        :prefix-icon="Search"
        @input="handleSearch"
      />
    </el-card>

    <!-- 统计信息 -->
    <el-row :gutter="20" class="stats-row" v-if="filteredSectors.length > 0">
      <el-col :xs="12" :sm="8" :md="8" :lg="8">
        <el-card class="stat-card">
          <div class="stat-value">{{ filteredSectors.length }}</div>
          <div class="stat-label">板块总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="8" :lg="8">
        <el-card class="stat-card up">
          <div class="stat-value">{{ upCount }}</div>
          <div class="stat-label">上涨板块</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="8" :lg="8">
        <el-card class="stat-card down">
          <div class="stat-value">{{ downCount }}</div>
          <div class="stat-label">下跌板块</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 板块卡片列表 -->
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
              <el-tag :type="sector.type === 'industry' ? 'success' : 'warning'" size="small">
                {{ sector.type === 'industry' ? '行业' : '概念' }}
              </el-tag>
            </div>
            <div class="sector-change" :class="getChangeClass(sector.change_pct)">
              {{ formatChange(sector.change_pct) }}
            </div>
          </div>

          <div class="sector-stats">
            <div class="stat-item">
              <span class="stat-label">个股数</span>
              <span class="stat-value">{{ sector.stock_count }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总成交量</span>
              <span class="stat-value">{{ formatVolume(sector.total_volume) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总成交额</span>
              <span class="stat-value">{{ formatAmount(sector.total_amount) }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

const sectors = ref([])
const loading = ref(false)
const searchQuery = ref('')
const filterType = ref('all')

// 过滤后的板块列表
const filteredSectors = computed(() => {
  let result = sectors.value

  // 按类型过滤
  if (filterType.value !== 'all') {
    result = result.filter(s => s.type === filterType.value)
  }

  // 按搜索词过滤
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(s =>
      s.name.toLowerCase().includes(query) ||
      s.code.toLowerCase().includes(query)
    )
  }

  return result
})

// 统计信息
const upCount = computed(() => filteredSectors.value.filter(s => s.change_pct > 0).length)
const downCount = computed(() => filteredSectors.value.filter(s => s.change_pct < 0).length)

// 获取板块列表
const fetchSectors = async () => {
  loading.value = true
  try {
    const response = await api.get('/sectors')
    if (response.success) {
      sectors.value = response.data || []
      ElMessage.success(`成功获取 ${sectors.value.length} 个板块`)
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

// 搜索处理（防抖）
let searchTimeout = null
const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    // 搜索逻辑已经在 computed 中处理
  }, 300)
}

// 跳转到板块详情
const goToSector = (sector) => {
  router.push({
    path: `/sector/${sector.code}`,
    query: {
      sectorType: sector.type,
      sectorName: sector.name
    }
  })
}

// 涨跌幅样式
const getChangeClass = (changePct) => {
  if (changePct > 0) return 'up'
  if (changePct < 0) return 'down'
  return 'flat'
}

// 板块卡片样式
const getSectorClass = (changePct) => {
  if (changePct > 0) return 'sector-up'
  if (changePct < 0) return 'sector-down'
  return 'sector-flat'
}

// 格式化涨跌幅显示
const formatChange = (changePct) => {
  if (changePct > 0) return `+${changePct.toFixed(2)}%`
  if (changePct < 0) return `${changePct.toFixed(2)}%`
  return '0.00%'
}

// 格式化成交量
const formatVolume = (volume) => {
  if (!volume) return '-'
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  }
  return volume.toString()
}

// 格式化成交额
const formatAmount = (amount) => {
  if (!amount) return '-'
  if (amount >= 100000000) {
    return '¥' + (amount / 100000000).toFixed(2) + '亿'
  } else if (amount >= 10000) {
    return '¥' + (amount / 10000).toFixed(2) + '万'
  }
  return '¥' + amount.toFixed(0)
}

onMounted(() => {
  fetchSectors()
})
</script>

<style scoped>
.sector-list-page {
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
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-card.up .stat-value {
  color: #f56c6c;
}

.stat-card.down .stat-value {
  color: #67c23a;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.sectors-container {
  min-height: 200px;
}

.sector-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
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
  border-color: #f56c6c;
}

.sector-card.sector-down {
  border-color: #67c23a;
}

.sector-card.sector-flat {
  border-color: #dcdfe6;
}

.sector-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.sector-info {
  flex: 1;
}

.sector-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.sector-code {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.sector-change {
  font-size: 20px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 6px;
}

.sector-change.up {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.sector-change.down {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}

.sector-change.flat {
  color: #909399;
  background: rgba(144, 147, 153, 0.1);
}

.sector-stats {
  display: flex;
  justify-content: space-between;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.stat-item {
  text-align: center;
}

.stat-item .stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-item .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

@media (max-width: 768px) {
  .sector-list-page {
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
