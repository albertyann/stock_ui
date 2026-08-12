<template>
  <el-card class="mt-20">
    <template #header>
      <div class="card-header">
        <span>所属分组</span>
        <el-button size="small" type="primary" link @click="$emit('switch-group')">
          换组
        </el-button>
      </div>
    </template>

    <div class="watchlist-info-grid">
      <div class="info-item">
        <span class="label">分组:</span>
        <span>{{ watchlistStockInfo.watchlist_name }}</span>
      </div>
      <div class="info-item" v-if="watchlistStockInfo.watch_date">
        <span class="label">关注日期:</span>
        <span>{{ watchlistStockInfo.watch_date }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  watchlistStockInfo: { type: Object, required: true }
})

defineEmits(['switch-group'])
</script>

<style scoped>
.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watchlist-info-grid {
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.watchlist-info-grid .info-item {
  display: flex;
  justify-content: space-between;
}

.watchlist-info-grid .info-item .label {
  color: var(--text-secondary);
}
</style>
