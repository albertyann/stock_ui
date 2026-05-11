<template>
  <div class="sector-heat-page">
    <div class="page-header">
      <h2>板块热度 - 概念板块</h2>
      <div class="header-actions">
        <el-button type="primary" @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filter">
        <el-form-item label="交易日期">
          <el-date-picker
            v-model="filter.trade_date"
            type="date"
            placeholder="选择交易日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
            style="width: 160px"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 统计信息 -->
      <div class="stats-row" v-if="meta.trade_date">
        <el-row :gutter="20">
          <el-col :xs="12" :sm="8" :md="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ meta.trade_date || '-' }}</div>
              <div class="stat-label">查询日期</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="8" :md="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ meta.total || 0 }}</div>
              <div class="stat-label">数据条数</div>
            </el-card>
          </el-col>

        </el-row>
      </div>
    </el-card>

    <!-- Tab 切换 -->
    <el-card v-loading="loading" class="data-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 上涨占比 Tab -->
        <el-tab-pane label="上涨占比" name="up_pct">
          <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
          <el-table
            v-if="tableData.length > 0"
            :data="tableData"
            style="width: 100%"
            :default-sort="{ prop: 'up_pct', order: 'descending' }"
            highlight-current-row
            border
            stripe
          >
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="rank" label="排名" width="80" sortable align="center">
              <template #default="{ row }">
                <el-tag :type="row.rank <= 3 ? 'danger' : row.rank <= 10 ? 'warning' : 'info'" effect="dark">
                  {{ row.rank }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sector_name" label="板块名称" min-width="160">
              <template #default="{ row }">
                <router-link
                  :to="{ path: '/concept/detail', query: { code: row.sector_code, sectorType: 'concept', sectorName: row.sector_name, tradeDate: meta.trade_date } }"
                  target="_blank"
                  class="sector-link"
                >{{ row.sector_name }}</router-link>
              </template>
            </el-table-column>
            <el-table-column prop="total_stocks" label="板块股票数" width="120" sortable align="center" />
            <el-table-column prop="up_stocks" label="上涨>1%股票数" width="140" sortable align="center" />
            <el-table-column prop="up_pct" label="上涨占比" width="120" sortable align="center">
              <template #default="{ row }">
                <span class="pct-value">{{ formatPct(row.up_pct) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 成交额排名 Tab -->
        <el-tab-pane label="成交额排名" name="amount">
          <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
          <el-table
            v-if="tableData.length > 0"
            :data="tableData"
            style="width: 100%"
            :default-sort="{ prop: 'total_amount', order: 'descending' }"
            highlight-current-row
            border
            stripe
          >
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="rank" label="排名" width="80" sortable align="center">
              <template #default="{ row }">
                <el-tag :type="row.rank <= 3 ? 'danger' : row.rank <= 10 ? 'warning' : 'info'" effect="dark">
                  {{ row.rank }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sector_name" label="板块名称" min-width="160">
              <template #default="{ row }">
                <router-link
                  :to="{ path: '/concept/detail', query: { code: row.sector_code, sectorType: 'concept', sectorName: row.sector_name, tradeDate: meta.trade_date } }"
                  target="_blank"
                  class="sector-link"
                >{{ row.sector_name }}</router-link>
              </template>
            </el-table-column>
            <el-table-column prop="total_stocks" label="板块股票数" width="120" sortable align="center" />
            <el-table-column prop="total_amount" label="总成交额(亿)" min-width="140" sortable align="right">
              <template #default="{ row }">
                <span class="amount-value">{{ formatAmount(row.total_amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="avg_amount" label="平均成交额(亿)" min-width="140" sortable align="right">
              <template #default="{ row }">
                <span>{{ formatAmount(row.avg_amount) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, TrendCharts } from '@element-plus/icons-vue'
import { basicDataApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const activeTab = ref('up_pct')
const meta = reactive({
  trade_date: null,
  tab: 'up_pct',
  total: 0
})

const filter = reactive({
  trade_date: ''
})

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await basicDataApi.getSectorHeat({
      trade_date: filter.trade_date || null,
      tab: activeTab.value,
      idx_type: '概念板块',
      min_stocks: 5
    })
    if (res.success) {
      tableData.value = res.data || []
      if (res.meta) {
        meta.trade_date = res.meta.trade_date
        meta.tab = res.meta.tab
        meta.total = res.meta.total
      }
      if (tableData.value.length > 0) {
        ElMessage.success(`成功获取 ${tableData.value.length} 条板块数据`)
      } else {
        ElMessage.info('暂无符合条件的板块数据')
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
      tableData.value = []
    }
  } catch (err) {
    console.error('Failed to fetch sector heat:', err)
    ElMessage.error('获取数据失败：' + (err.message || '网络错误'))
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const handleTabChange = (tab) => {
  activeTab.value = tab
  fetchData()
}

const resetFilter = () => {
  filter.trade_date = ''
  activeTab.value = 'up_pct'
  fetchData()
}

const formatAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  return (amount / 1e8).toFixed(2)
}

const formatPct = (value) => {
  if (value === null || value === undefined) return '-'
  return value.toFixed(2) + '%'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.sector-heat-page {
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

.filter-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.stat-card {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.data-card {
  min-height: 200px;
}

.sector-link {
  color: #409eff;
  text-decoration: none;
}
.sector-link:hover {
  text-decoration: underline;
}

.amount-value {
  color: #409eff;
  font-weight: 600;
}

.pct-value {
  color: #f56c6c;
  font-weight: 600;
}

@media (max-width: 768px) {
  .sector-heat-page {
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
}
</style>
