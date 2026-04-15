<template>
  <div class="page-container">
    <div class="page-header">
      <h2>交易日历</h2>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="交易所">
          <el-select
            v-model="filter.exchange"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleFilterChange"
          >
            <el-option
              v-for="item in exchanges"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="filter.cal_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            clearable
            @change="handleFilterChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="tableData" stripe border>
        <el-table-column prop="exchange" label="交易所" width="120" />
        <el-table-column prop="cal_date" label="日期" width="150" />
        <el-table-column prop="is_open" label="是否开市" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_open ? 'success' : 'danger'">
              {{ row.is_open ? '开市' : '休市' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pretrade_date" label="前一个交易日" width="150" />
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
const exchanges = ref([])

const filter = reactive({
  exchange: '',
  cal_date: ''
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
    const res = await basicDataApi.getTradeCal({
      page: pagination.page,
      page_size: pagination.page_size,
      exchange: filter.exchange || null,
      cal_date: filter.cal_date || null
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

const fetchExchanges = async () => {
  try {
    const res = await basicDataApi.getExchanges()
    if (res.success) {
      exchanges.value = res.data || []
    }
  } catch (err) {
    console.error(err)
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

const resetFilter = () => {
  filter.exchange = ''
  filter.cal_date = ''
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
  fetchExchanges()
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
  color: #303133;
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
</style>
