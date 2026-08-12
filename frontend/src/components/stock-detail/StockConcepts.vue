<template>
  <!-- 概念板块 -->
  <el-card class="mt-20" v-loading="conceptLoading">
    <template #header>
      <div class="card-header">
        <span>概念板块</span>
        <span v-if="conceptList.length > 0" class="signal-count">{{ conceptList.length }}个</span>
      </div>
    </template>
    <div v-if="conceptList.length > 0" class="concept-tags">
      <router-link
        v-for="c in conceptList"
        :key="c.ts_code"
        :to="{ path: '/concept/detail', query: { code: c.ts_code, sectorType: 'concept', sectorName: c.name } }"
        custom
        v-slot="{ navigate }"
      >
        <el-tag
          size="small"
          effect="plain"
          class="concept-tag"
          :type="c.change_pct > 0 ? 'danger' : c.change_pct < 0 ? 'success' : 'info'"
          @click="navigate"
        >
          {{ c.name }}
        </el-tag>
      </router-link>
    </div>
    <el-empty v-else description="暂无概念板块数据" :image-size="60" />
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { sectorApi } from '@/api'

const props = defineProps({
  tsCode: {
    type: String,
    required: true
  }
})

const conceptList = ref([])
const conceptLoading = ref(false)

const loadConcepts = async () => {
  conceptLoading.value = true
  try {
    const response = await sectorApi.getStockConcepts(props.tsCode)
    if (response.success) {
      conceptList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load concepts:', error)
  } finally {
    conceptLoading.value = false
  }
}

onMounted(() => {
  loadConcepts()
})
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

.signal-count {
  font-size: 12px;
  color: var(--text-muted);
}

.concept-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.concept-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.concept-tag:hover {
  opacity: 0.8;
}
</style>
