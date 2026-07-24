<template>
  <div class="page-container">
    <div v-if="etfInfo" class="etf-detail">
      <el-page-header
        @back="$router.back()"
        :content="`${etfInfo.csname} (${etfInfo.ts_code})`"
      />

      <el-card class="etf-info-card mt-20">
        <div class="etf-info-grid">
          <div class="info-item">
            <span class="info-label">中文全称</span>
            <span class="info-value">{{ etfInfo.cname || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">跟踪指数</span>
            <span class="info-value">{{ etfInfo.index_name || '-' }} ({{ etfInfo.index_code || '-' }})</span>
          </div>
          <div class="info-item">
            <span class="info-label">交易所</span>
            <span class="info-value">{{ etfInfo.exchange || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">ETF类型</span>
            <span class="info-value">{{ etfInfo.etf_type || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">上市日期</span>
            <span class="info-value">{{ etfInfo.list_date || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">管理费率</span>
            <span class="info-value">{{ etfInfo.mgt_fee != null ? (etfInfo.mgt_fee * 100).toFixed(2) + '%' : '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">管理人</span>
            <span class="info-value">{{ etfInfo.mgr_name || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">上市状态</span>
            <span class="info-value">
              <el-tag v-if="etfInfo.list_status === 'L'" size="small" type="success">上市</el-tag>
              <el-tag v-else-if="etfInfo.list_status === 'D'" size="small" type="danger">退市</el-tag>
              <el-tag v-else-if="etfInfo.list_status === 'P'" size="small" type="warning">暂停</el-tag>
              <span v-else>{{ etfInfo.list_status }}</span>
            </span>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20" class="mt-20">
        <el-col :span="24">
          <el-card v-loading="klineLoading">
            <template #header>
              <div class="card-header">
                <span>日K线（{{ klineData.length }}条）</span>
              </div>
            </template>
            <StockKlineChart
              :tsCode="props.tsCode"
              :klineData="klineData"
              engine="klc"
              height="400px"
              :showVolume="true"
            />
          </el-card>
        </el-col>
      </el-row>

      <el-card class="mt-20" v-loading="constituentsLoading">
        <template #header>
          <div class="card-header">
            <span>成分股</span>
            <span class="signal-count" v-if="constituents.length > 0">共 {{ constituents.length }} 只</span>
          </div>
        </template>

        <el-table v-if="constituents.length > 0" :data="constituents" stripe border size="small">
          <el-table-column prop="con_code" label="成分股代码" width="130" />
          <el-table-column prop="con_name" label="成分股名称" width="150" />
          <el-table-column prop="qty" label="持仓数量" width="120" align="right">
            <template #default="{ row }">
              {{ row.qty != null ? row.qty.toLocaleString() : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="cpr" label="申赎保证金率(%)" width="130" align="right">
            <template #default="{ row }">
              {{ row.cpr != null ? row.cpr.toFixed(2) + '%' : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="rdr" label="赎回保证金率(%)" width="130" align="right">
            <template #default="{ row }">
              {{ row.rdr != null ? row.rdr.toFixed(2) + '%' : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="sub_flag" label="类型" width="80" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.sub_flag === 'S'" size="small" type="success">实物</el-tag>
              <el-tag v-else-if="row.sub_flag === 'C'" size="small" type="warning">现金</el-tag>
              <span v-else>{{ row.sub_flag || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="trade_date" label="更新日期" width="120" />
        </el-table>
        <el-empty v-else description="暂无成分股数据" :image-size="60" />
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
import { ref, onMounted } from 'vue'
import { basicDataApi } from '@/api'
import StockKlineChart from '@/components/StockKlineChart.vue'

const props = defineProps(['tsCode'])

const etfInfo = ref(null)
const klineData = ref([])
const constituents = ref([])
const klineLoading = ref(false)
const constituentsLoading = ref(false)
const loadError = ref('')

const loadData = async () => {
  loadError.value = ''

  // Load ETF basic info
  try {
    const res = await basicDataApi.getEtfBasic({ ts_code: props.tsCode })
    if (res.success && res.data && res.data.length > 0) {
      etfInfo.value = res.data[0]
    } else {
      loadError.value = '未找到该ETF信息'
      return
    }
  } catch (err) {
    loadError.value = '获取ETF信息失败'
    return
  }

  // Load K-line data
  klineLoading.value = true
  try {
    const res = await basicDataApi.getEtfDailyKline(props.tsCode, 180)
    if (res.success) {
      klineData.value = res.data || []
    }
  } catch (err) {
    console.error('Failed to load ETF kline:', err)
  } finally {
    klineLoading.value = false
  }

  // Load constituent stocks
  constituentsLoading.value = true
  try {
    const res = await basicDataApi.getEtfConstituents(props.tsCode)
    if (res.success) {
      constituents.value = res.data || []
    }
  } catch (err) {
    console.error('Failed to load ETF constituents:', err)
  } finally {
    constituentsLoading.value = false
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
.etf-info-card {
  margin-bottom: 0;
}
.etf-info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.info-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.signal-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
