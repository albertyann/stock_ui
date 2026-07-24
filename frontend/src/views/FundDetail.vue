<template>
  <div class="page-container">
    <div v-if="fundInfo" class="fund-detail">
      <el-page-header
        @back="$router.back()"
        :content="`${fundInfo.name} (${fundInfo.ts_code})`"
      />

      <el-card class="mt-20">
        <template #header>
          <div class="card-header">
            <span>持仓明细</span>
            <span class="data-count" v-if="holdings.length > 0">
              共 {{ periodList.length }} 个报告期
            </span>
          </div>
        </template>

        <div v-if="periodList.length > 0">
          <el-tabs v-model="activePeriod" type="card" @tab-change="handlePeriodChange">
            <el-tab-pane
              v-for="period in periodList"
              :key="period"
              :label="period"
              :name="period"
            />
          </el-tabs>

          <el-table
            v-loading="loading"
            :data="currentHoldings"
            stripe
            border
            size="small"
          >
            <el-table-column prop="symbol" label="股票代码" width="130" />
            <el-table-column prop="stk_mkv_ratio" label="占净值比例(%)" width="130" align="right">
              <template #default="{ row }">
                {{ row.stk_mkv_ratio != null ? row.stk_mkv_ratio.toFixed(2) + '%' : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="mkv" label="持仓市值(元)" width="150" align="right">
              <template #default="{ row }">
                {{ row.mkv != null ? row.mkv.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="持仓数量" width="130" align="right">
              <template #default="{ row }">
                {{ row.amount != null ? row.amount.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="stk_float_ratio" label="占流通比例(%)" width="130" align="right">
              <template #default="{ row }">
                {{ row.stk_float_ratio != null ? row.stk_float_ratio.toFixed(2) + '%' : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="ann_date" label="公告日期" width="120" />
          </el-table>
        </div>

        <el-empty v-else description="暂无持仓数据" :image-size="60" />
      </el-card>
    </div>

    <div v-else-if="loadError" class="mt-20">
      <el-result status="error" title="加载失败" :sub-title="loadError">
        <template #extra>
          <el-button type="primary" @click="loadData">重新加载</el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="mt-20" v-loading="true">
      <el-empty description="加载中..." :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { basicDataApi } from '@/api'

const props = defineProps(['tsCode'])

const fundInfo = ref(null)
const holdings = ref([])
const loading = ref(false)
const loadError = ref('')
const activePeriod = ref('')

const periodList = computed(() => {
  const periods = [...new Set(holdings.value.map((h) => h.end_date))]
  return periods.sort((a, b) => b.localeCompare(a))
})

const currentHoldings = computed(() => {
  if (!activePeriod.value) return []
  return holdings.value.filter((h) => h.end_date === activePeriod.value)
})

const handlePeriodChange = () => {
  // tab切换不需要重新加载
}

const loadData = async () => {
  loadError.value = ''
  loading.value = true

  try {
    // Load fund basic info
    const infoRes = await basicDataApi.getFundBasic({ ts_code: props.tsCode })
    if (infoRes.success && infoRes.data && infoRes.data.length > 0) {
      fundInfo.value = infoRes.data[0]
    }

    // Load portfolio holdings
    const portRes = await basicDataApi.getFundPortfolio(props.tsCode)
    if (portRes.success) {
      holdings.value = portRes.data || []
      if (holdings.value.length > 0) {
        activePeriod.value = periodList.value[0]
      }
    } else {
      loadError.value = portRes.error || '获取持仓数据失败'
    }
  } catch (err) {
    loadError.value = '加载基金详情失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.tsCode) {
    loadData()
  }
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.mt-20 {
  margin-top: 20px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.data-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
