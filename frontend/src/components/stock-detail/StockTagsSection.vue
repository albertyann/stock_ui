<template>
  <el-card class="mt-20">
    <template #header>
      <div class="card-header">
        <span>标签</span>
        <el-button size="small" type="primary" link @click="$emit('edit')">
          <el-icon><EditPen /></el-icon>编辑
        </el-button>
      </div>
    </template>

    <div class="tags-display">
      <template v-if="tags.length > 0">
        <el-tag
          v-for="tag in tags"
          :key="tag"
          size="small"
          effect="plain"
          class="stock-tag"
        >
          {{ tag }}
        </el-tag>
      </template>
      <el-tag
        v-else
        size="small"
        type="info"
        effect="plain"
        class="stock-tag empty-tag"
      >
        暂无标签
      </el-tag>
    </div>
  </el-card>
</template>

<script setup>
import { EditPen } from '@element-plus/icons-vue'

defineProps({
  tags: { type: Array, default: () => [] }
})

defineEmits(['edit'])
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

/* 标签显示 */
.tags-display {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stock-tag {
  margin-right: 0;
}

.empty-tag {
  color: var(--text-muted);
}
</style>
