<template>
  <div class="stock-calculator">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>股票计算器</span>
        </div>
      </template>

      <el-form :inline="false" label-width="100px" class="calc-form">
        <el-form-item label="价格 A">
          <el-input-number
            v-model="priceA"
            :precision="2"
            :step="0.01"
            :min="0"
            placeholder="输入价格 A"
            controls-position="right"
            style="width: 300px"
          />
        </el-form-item>
        <el-form-item label="价格 B">
          <el-input-number
            v-model="priceB"
            :precision="2"
            :step="0.01"
            :min="0"
            placeholder="输入价格 B"
            controls-position="right"
            style="width: 300px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="calculate">计算涨幅</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result !== null" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>计算结果</span>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="价格 A">{{ formatPrice(priceA) }}</el-descriptions-item>
        <el-descriptions-item label="价格 B">{{ formatPrice(priceB) }}</el-descriptions-item>
        <el-descriptions-item label="价差 (A - B)">
          <span>{{ formatPrice(priceA - priceB) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="涨幅 (A-B)/B">
          <span :class="result > 0 ? 'up' : result < 0 ? 'down' : ''">
            {{ formatPct(result) }}
          </span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const priceA = ref(null)
const priceB = ref(null)
const result = ref(null)

const calculate = () => {
  if (priceA.value === null || priceB.value === null) {
    ElMessage.warning('请输入两个价格')
    return
  }
  if (priceB.value === 0) {
    ElMessage.warning('价格 B 不能为 0')
    return
  }
  result.value = (priceA.value - priceB.value) / priceB.value * 100
}

const reset = () => {
  priceA.value = null
  priceB.value = null
  result.value = null
}

const formatPrice = (price) => {
  if (price === null || price === undefined) return '-'
  return Number(price).toFixed(2)
}

const formatPct = (pct) => {
  if (pct === null || pct === undefined) return '-'
  const val = Number(pct)
  return (val > 0 ? '+' : '') + val.toFixed(2) + '%'
}
</script>

<style scoped>
.stock-calculator {
  padding: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.calc-form {
  max-width: 500px;
}

.up {
  color: #f56c6c;
  font-weight: 500;
}

.down {
  color: #67c23a;
  font-weight: 500;
}
</style>
