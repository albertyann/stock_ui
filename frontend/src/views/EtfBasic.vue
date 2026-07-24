<template>
  <div class="page-container">
    <div class="page-header">
      <h2>ETF管理</h2>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="ETF名称">
          <el-input
            v-model="filter.name"
            placeholder="输入ETF名称"
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
            <router-link :to="`/etf/${row.ts_code}`" class="ts-code-link">
              {{ row.ts_code }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="csname" label="ETF简称" width="130" />
        <el-table-column prop="cname" label="中文全称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="index_code" label="跟踪指数代码" width="130" />
        <el-table-column prop="index_name" label="跟踪指数名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="setup_date" label="成立日期" width="110" />
        <el-table-column prop="list_date" label="上市日期" width="110" />
        <el-table-column prop="list_status" label="上市状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.list_status === 'L'" type="success">上市</el-tag>
            <el-tag v-else-if="row.list_status === 'D'" type="danger">退市</el-tag>
            <el-tag v-else-if="row.list_status === 'P'" type="warning">暂停</el-tag>
            <span v-else>{{ row.list_status }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="exchange" label="交易所" width="80" />
        <el-table-column prop="etf_type" label="ETF类型" width="100" />
        <el-table-column prop="mgr_name" label="管理人" min-width="150" show-overflow-tooltip />
        <el-table-column prop="mgt_fee" label="管理费率" width="100">
          <template #default="{ row }">
            {{ row.mgt_fee != null ? (row.mgt_fee * 100).toFixed(2) + '%' : '-' }}
          </template>
        </el-table-column>
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
  ts_code: ''
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
    const res = await basicDataApi.getEtfBasic({
      page: pagination.page,
      page_size: pagination.page_size,
      name: filter.name || null,
      ts_code: filter.ts_code || null
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
}
</style>
