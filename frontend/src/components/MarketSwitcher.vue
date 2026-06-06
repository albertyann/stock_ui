<template>
  <div class="market-switcher">
    <el-button-group>
      <el-button
        :type="marketStore.isA ? 'primary' : 'default'"
        size="small"
        @click="marketStore.setMarket('A')"
      >
        A股
      </el-button>
      <el-button
        :type="marketStore.isHK ? 'primary' : 'default'"
        size="small"
        @click="marketStore.setMarket('HK')"
      >
        港股
      </el-button>
    </el-button-group>
  </div>
</template>

<script setup>
import { useMarketStore } from '@/stores/market'

const marketStore = useMarketStore()
</script>

<style scoped>
.market-switcher {
  display: flex;
  align-items: center;
}
</style>
