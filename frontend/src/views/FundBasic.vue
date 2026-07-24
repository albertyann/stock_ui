<template>
  <div class="page-container">
    <div class="page-header">
      <h2>基金管理</h2>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="基金名称">
          <el-input
            v-model="filter.name"
            placeholder="输入基金名称"
            clearable
            @keyup.enter="handleFilterChange"
            @clear="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="TS代码">
          <el-input
            v-model="filter.ts_code"
            placeholder="输入ts_code"
            clearable
            @keyup.enter="handleFilterChange"
            @clear="handleFilterChange"
          />
        </el-form-item>
        <el-form-item label="基金类型">
          <el-select
            v-model="filter.fund_type"
            placeholder="选择类型"
            clearable
            @change="handleFilterChange"
          >
            <el-option label="全部" value="" />
            <el-option label="股票型" value="股票型" />
            <el-option label="混合型" value="混合型" />
            <el-option label="债券型" value="债券型" />
            <el-option label="货币型" value="货币型" />
            <el-option label="指数型" value="指数型" />
            <el-option label="QDII" value="QDII" />
            <el-option label="FOF" value="FOF" />
            <el-option label="REITs" value="REITs" />
          </el-select>
        </el-form-item>
        <el-form-item label="市场">
          <el-select
            v-model="filter.market"
            placeholder="选择市场"
            clearable
            @change="handleFilterChange"
          >
            <el-option label="全部" value="" />
            <el-option label="E场内" value="E" />
            <el-option label="O场外" value="O" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilterChange">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="tableData" stripe border>
        <el-table-column label="TS代码" width="130">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" class="ts-code-link" @click="$router.push(`/fund/${row.ts_code}`)">
              {{ row.ts_code }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="基金名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="fund_type" label="基金类型" width="90" />
        <el-table-column prop="management" label="管理人" min-width="160" show-overflow-tooltip />
        <el-table-column prop="custodian" label="托管人" min-width="140" show-overflow-tooltip />
        <el-table-column prop="found_date" label="成立日期" width="110" />
        <el-table-column prop="list_date" label="上市日期" width="110" />
        <el-table-column prop="market" label="市场" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.market === 'E'" type="primary">场内</el-tag>
            <el-tag v-else-if="row.market === 'O'" type="success">场外</el-tag>
            <span v-else>{{ row.market }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'L'" type="success">上市</el-tag>
            <el-tag v-else-if="row.status === 'D'" type="danger">摘牌</el-tag>
            <el-tag v-else-if="row.status === 'I'" type="warning">发行</el-tag>
            <span v-else>{{ row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="m_fee" label="管理费" width="90">
          <template #default="{ row }">
            {{ row.m_fee != null ? row.m_fee.toFixed(2) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="invest_type" label="投资类型" width="120" show-overflow-tooltip />
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { basicDataApi } from '@/api'

const loading = ref(false)
const tableData = ref([])

const filter = reactive({
  name: '',
  ts_code: '',
  fund_type: '',
  market: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await basicDataApi.getFundBasic({
      page: pagination.page,
      page_size: pagination.page_size,
      name: filter.name || null,
      ts_code: filter.ts_code || null,
      fund_type: filter.fund_type || null,
      market: filter.market || null
    })
    if (res.success) {
      tableData.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total
        pagination.total_pages = res.pagination.total_pages
      }
    } else {
      ElMessage.error(res.error || '获取数据失败')
    }
  } catch (err) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

const resetFilter = () => {
  filter.name = ''
  filter.ts_code = ''
  filter.fund_type = ''
  filter.market = ''
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
}
.filter-card {
  margin-bottom: 20px;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.ts-code-link {
  font-family: monospace;
}
</style>
