<template>
  <div class="sector-trend-page">
    <div class="page-header">
      <h2>板块趋势</h2>
      <el-text type="info">
        统计关注列表各板块近20个交易日上涨股票占比变化
      </el-text>
    </div>

    <!-- 趋势折线图 -->
    <SectorTrendChart ref="trendChartRef" />

    <!-- 板块成交量折线图 -->
    <SectorVolumeChart />

    <!-- 超涨分布折线图 -->
    <SectorSuperRiseChart />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SectorTrendChart from '@/components/SectorTrendChart.vue'
import SectorVolumeChart from '@/components/SectorVolumeChart.vue'
import SectorSuperRiseChart from '@/components/SectorSuperRiseChart.vue'

const trendChartRef = ref(null)
</script>

<style scoped>
.sector-trend-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #303133;
}


</style>
