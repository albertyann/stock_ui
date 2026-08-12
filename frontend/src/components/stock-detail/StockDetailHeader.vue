<template>
  <el-page-header
    @back="$router.back()"
    :content="`${stock.name}(${stock.ts_code})${stock.industry ? ' - ' + stock.industry : ''}`"
  />

  <!-- 股票信息顶栏 -->
  <el-card class="stock-info-top mt-20">
    <div class="stock-info-top__inner">
      <div class="stock-info-top__price-block">
        <span class="stock-info-top__price">¥{{ stock.current_price?.toFixed(2) }}</span>
        <span class="stock-info-top__change" :class="getChangeClass(stock.change_pct)">
          {{ stock.change_pct > 0 ? '+' : '' }}{{ stock.change_pct?.toFixed(2) }}%
        </span>
        <el-tag size="small" :type="boardType.type" class="board-tag">
          {{ boardType.emoji }} {{ boardType.label }}
        </el-tag>
      </div>
      <div class="stock-info-top__metrics">
        <div class="stock-info-top__metric">
          <el-tooltip placement="bottom" :content="volumeTooltipText">
            <div class="stock-info-top__metric-tooltip-wrapper">
              <span class="metric-label">成交量</span>
              <span class="metric-value">{{ formatVolume(stock.volume) }}</span>
            </div>
          </el-tooltip>
        </div>
        <div class="stock-info-top__metric">
          <span class="metric-label">成交额</span>
          <span class="metric-value">{{ formatAmount(stock.amount) }}</span>
        </div>
        <div class="stock-info-top__metric">
          <span class="metric-label">换手率</span>
          <span class="metric-value">{{ stock.turnover_rate?.toFixed(2) }}%</span>
        </div>
        <div class="stock-info-top__metric">
          <span class="metric-label">市盈率</span>
          <span class="metric-value">{{ stock.pe?.toFixed(2) || '-' }}</span>
        </div>
        <div class="stock-info-top__metric">
          <span class="metric-label">市净率</span>
          <span class="metric-value">{{ stock.pb?.toFixed(2) || '-' }}</span>
        </div>
        <div class="stock-info-top__metric">
          <span class="metric-label">总市值</span>
          <span class="metric-value">{{ formatMarketCap(stock.market_cap) }}</span>
        </div>
      </div>
      <div class="stock-info-top__actions">
        <el-button size="small" :type="isWatched ? 'info' : 'warning'" link @click="$emit('open-follow')" :disabled="isWatched">
          {{ isWatched ? '已关注' : '关注' }}
        </el-button>
        <el-button size="small" type="primary" link @click="openXueqiu(stock)">
          雪球
        </el-button>
        <el-button size="small" link @click="$emit('open-settings')">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { Setting } from '@element-plus/icons-vue'
import { openXueqiu, formatMarketCap } from '@/utils/stock'

const props = defineProps({
  stock: { type: Object, required: true },
  isWatched: { type: Boolean, default: false },
  volumeTooltipText: { type: String, default: '' }
})

defineEmits(['open-follow', 'open-settings'])

// 板块类型计算属性
const boardType = computed(() => {
  if (!props.stock?.ts_code) return { emoji: '', label: '', type: 'info' }

  const code = props.stock.ts_code.split('.')[0]
  const prefix = code.substring(0, 3)

  // 科创板
  if (['688', '689'].includes(prefix)) {
    return { emoji: '⭐', label: '科创板', type: 'warning' }
  }
  // 创业板
  if (['300', '301'].includes(prefix)) {
    return { emoji: '🚀', label: '创业板', type: 'success' }
  }
  // 北交所
  if (prefix.startsWith('8') || ['430', '831', '832', '833', '834', '835', '836', '837', '838', '839', '870', '871', '872', '873'].includes(prefix)) {
    return { emoji: '🏢', label: '北交所', type: 'danger' }
  }
  // 主板 (600/601/603/605/000/001/002/003)
  return { emoji: '🏛️', label: '主板', type: 'info' }
})

// 注: 与 utils/stock 的 getChangeClass 不同, 空值返回 '' 而非 'flat'
const getChangeClass = (change) => {
  if (!change) return ''
  return change > 0 ? 'up' : change < 0 ? 'down' : ''
}

// 注: 与 utils/stock 的 formatVolume/formatAmount 阈值边界不同 (> 而非 >=), 保持原行为
const formatVolume = (volume) => {
  if (!volume) return '-'
  if (volume > 100000000) return (volume / 100000000).toFixed(2) + '亿'
  if (volume > 10000) return (volume / 10000).toFixed(2) + '万'
  return volume.toString()
}

const formatAmount = (amount) => {
  if (!amount) return '-'
  if (amount > 100000000) return (amount / 100000000).toFixed(2) + '亿'
  if (amount > 10000) return (amount / 10000).toFixed(2) + '万'
  return amount.toString()
}
</script>

<style scoped>
.mt-20 {
  margin-top: 20px;
}

/* 顶部股票信息栏 */
.stock-info-top :deep(.el-card__body) {
  padding: 16px 24px;
}

.stock-info-top__inner {
  display: flex;
  align-items: center;
  gap: 32px;
}

.stock-info-top__price-block {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-shrink: 0;
}

.stock-info-top__price {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.stock-info-top__change {
  font-size: 16px;
  font-weight: 600;
}

.stock-info-top__change.up {
  color: var(--stock-up);
}

.stock-info-top__change.down {
  color: var(--stock-down);
}

.stock-info-top__metrics {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  flex: 1;
}

.stock-info-top__metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-info-top__metric-tooltip-wrapper {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-info-top__metric .metric-label {
  font-size: 12px;
  color: var(--text-muted);
}

.stock-info-top__metric .metric-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.stock-info-top__actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stock-info-top__price-block .board-tag {
  margin-left: 8px;
}
</style>
