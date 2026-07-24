<template>
  <div class="page-container">
    <div class="page-header">
      <h2>指数管理</h2>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="指数名称">
          <el-input
            v-model="filter.name"
            placeholder="输入指数名称"
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
        <el-form-item label="市场">
          <el-select
            v-model="filter.market"
            placeholder="选择市场"
            clearable
            @change="handleFilterChange"
          >
            <el-option label="沪深" value="沪深" />
            <el-option label="上证" value="上证" />
            <el-option label="深证" value="深证" />
            <el-option label="中证" value="中证" />
            <el-option label="国证" value="国证" />
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
            <router-link :to="`/index/${row.ts_code}`" class="ts-code-link">
              {{ row.ts_code }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="简称" width="100">
          <template #default="{ row }">
            <el-tooltip :content="row.fullname" placement="top" effect="dark">
              <span>{{ row.name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="market" label="市场" width="70" />
        <el-table-column prop="publisher" label="发布方" width="300" />
        <el-table-column prop="index_type" label="指数风格" width="90" />
        <el-table-column prop="category" label="指数类别" width="90" />
        <el-table-column prop="base_date" label="基期" width="100" />
        <el-table-column prop="base_point" label="基点" width="80" />
        <el-table-column prop="list_date" label="发布日期" width="100" />
        <el-table-column prop="weight_rule" label="加权方式" width="90" />
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
    const res = await basicDataApi.getIndexBasic({
      page: pagination.page,
      page_size: pagination.page_size,
      name: filter.name || null,
      ts_code: filter.ts_code || null,
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
  color: var(--el-color-primary);
  text-decoration: none;
  cursor: pointer;
}
.ts-code-link:hover {
  text-decoration: underline;
  color: var(--el-color-primary-light-3);
}
</style>
