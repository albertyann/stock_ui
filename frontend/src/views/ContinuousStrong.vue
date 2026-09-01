<template>
  <div class="page-container">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="策略">
          <el-select v-model="filter.strategy_name" style="width: 220px" disabled>
            <el-option label="RsiStrong" value="RsiStrong" />
          </el-select>
        </el-form-item>
        <el-form-item label="连续天数">
          <el-select v-model="filter.days" style="width: 120px" @change="handleFilterChange">
            <el-option v-for="n in [2, 3, 4, 5]" :key="n" :label="`${n} 天`" :value="n" />
          </el-select>
        </el-form-item>
        <el-form-item label="最低评分">
          <el-input-number
            v-model="filter.min_score"
            :min="1"
            :max="100"
            :step="1"
            @change="handleFilterChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">查询</el-button>
        </el-form-item>
      </el-form>
      <div v-if="dates.length > 0" class="date-range-info">
        <span>统计区间：</span>
        <el-tag v-for="d in dates" :key="d" size="small" class="date-tag">{{ d }}</el-tag>
      </div>
    </el-card>

    <el-card v-loading="loading">
      <el-empty v-if="!loading && stocks.length === 0" description="暂无连续强势信号" />

      <el-table
        v-if="stocks.length > 0"
        :data="pagedStocks"
        stripe
        :default-sort="{ prop: 'avg_score', order: 'descending' }"
      >
        <el-table-column label="代码" width="130">
          <template #default="{ row }">
            <span class="stock-code">{{ row.ts_code }}</span>
          </template>
        </el-table-column>
        <el-table-column label="名称" min-width="130">
          <template #default="{ row }">
            <span class="stock-name">{{ row.name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="市场" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="getMarketTypeTag(row.ts_code)">
              {{ getMarketType(row.ts_code) || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="行业" min-width="120">
          <template #default="{ row }">
            <span>{{ row.industry || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column
          v-for="d in dates"
          :key="d"
          :label="`${d} 评分`"
          min-width="130"
          align="center"
        >
          <template #default="{ row }">
            <span :class="getScoreClass(row.scores?.[d])">{{ formatScore(row.scores?.[d]) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="平均分" prop="avg_score" width="100" sortable align="center">
          <template #default="{ row }">
            <span class="avg-score">{{ formatScore(row.avg_score) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="连续天数" prop="days_continuous" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="success">{{ row.days_continuous }} 天</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="viewDetail(row)">详情</el-button>
            <el-button type="primary" size="small" link @click="openXueqiu(row)">雪球</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { screeningApi } from '@/api'
import { getMarketType, getMarketTypeTag, openXueqiu } from '@/utils/stock'

const loading = ref(false)
const stocks = ref([])
const dates = ref([])

const filter = reactive({
  strategy_name: 'RsiStrong',
  days: 2,
  min_score: 95
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const pagedStocks = computed(() => {
  const start = (pagination.page - 1) * pagination.page_size
  return stocks.value.slice(start, start + pagination.page_size)
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await screeningApi.getStrongContinuous({
      strategy_name: filter.strategy_name,
      days: filter.days,
      min_score: filter.min_score
    })
    if (res.success) {
      stocks.value = res.data || []
      dates.value = res.dates || []
      pagination.total = stocks.value.length
    } else {
      ElMessage.error(res.error || '获取数据失败')
    }
  } catch (err) {
    console.error('Failed to fetch strong continuous signals:', err)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page) => {
  pagination.page = page
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
}

const viewDetail = (stock) => {
  if (!stock.ts_code) return
  window.open(`/stock/${stock.ts_code}`, '_blank')
}

const formatScore = (val) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(2)
}

const getScoreClass = (val) => {
  if (val === null || val === undefined) return ''
  return Number(val) >= filter.min_score ? 'score-high' : 'score-mid'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.date-range-info {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-muted);
}

.date-tag {
  margin-left: 6px;
}

.stock-code {
  font-size: 13px;
  color: var(--text-muted);
}

.stock-name {
  font-weight: 600;
  color: var(--text-primary);
}

.avg-score {
  font-weight: 600;
  color: var(--accent);
}

.score-high {
  color: var(--stock-up);
  font-weight: 600;
}

.score-mid {
  color: var(--text-primary);
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
