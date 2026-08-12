<template>
  <div>
    <div class="stock-detail" v-if="stock">
      <StockDetailHeader
        :stock="stock"
        :is-watched="isWatched"
        :volume-tooltip-text="volumeTooltipText"
        @open-follow="openFollowDialog"
        @open-settings="showSettingsDialog = true"
      />

      <StockMainKline
        :ts-code="props.tsCode"
        v-model:adj-type="adjType"
        :buy-signals-data="buySignalsData"
        :adjusted-kline-data="adjustedKlineData"
        :indicator-kline-data="indicatorKlineData"
        :adjusted-weekly-kline-data="adjustedWeeklyKlineData"
        :kline-indicator-settings="klineIndicatorSettings"
        :eval-loading="evalLoading"
        :eval-scores="highEvalScores"
        @open-indicator-settings="openKlineIndicatorDialog"
        @open-eval="openEvalDialog"
      >
        <template #daily-append>
          <!-- 信号时间线 -->
          <StockSignalTimeline
            ref="signalTimelineRef"
            :tsCode="props.tsCode"
            @open-notes="openNotesDialog"
          />

          <!-- AI 调研记录 -->
          <StockSurveyList
            ref="surveyListRef"
            :tsCode="props.tsCode"
          />
        </template>

        <template #weekly-append>
          <!-- 概念板块 -->
          <StockConcepts :tsCode="props.tsCode" />

          <!-- 标签管理 -->
          <StockTagsSection :tags="stockTags" @edit="openTagPopover" />

          <!-- 审计意见 + 季度业绩 -->
          <StockFinancials :tsCode="props.tsCode" />

          <!-- 资金流向 -->
          <StockMoneyflowChart :tsCode="props.tsCode" />

          <!-- 筹码分布 -->
          <StockChipDistribution ref="chipDistRef" :tsCode="props.tsCode" />

          <!-- 所属分组 -->
          <StockWatchlistInfo
            v-if="watchlistStockInfo"
            :watchlist-stock-info="watchlistStockInfo"
            @switch-group="openSwitchGroupDialog"
          />

          <!-- 股票信息 -->
          <StockInfoSection :ts-code="props.tsCode" :stock="stock" />

          <!-- 指标说明 -->
          <StockIndicatorGuide />
        </template>
      </StockMainKline>
    </div>

    <el-empty v-else description="加载中..." />

    <!-- 编辑备注弹窗 -->
    <StockNotesDialog
      v-model="showNotesDialog"
      :stock="stock"
      @saved="onNotesSaved"
    />

    <!-- 切换分组弹窗 -->
    <SwitchGroupDialog
      v-model="showSwitchGroupDialog"
      :stock="stock"
      :watchlist-stock-info="watchlistStockInfo"
      @switched="loadWatchlistStockInfo"
    />

    <!-- 编辑标签弹窗 -->
    <StockTagsDialog
      v-model="tagPopoverVisible"
      :ts-code="props.tsCode"
      :stock="stock"
      :tags="stockTags"
      @saved="onTagsSaved"
    />

    <!-- 关注股票弹窗 -->
    <FollowStockDialog
      v-model="followDialogVisible"
      :stock="currentFollowStock"
      @success="handleFollowSuccess"
    />

    <!-- 设置弹窗 -->
    <StockSettingsDialog
      v-model="showSettingsDialog"
      :ts-code="props.tsCode"
      :stock="stock"
      :watchlist-stock-info="watchlistStockInfo"
      @kline-synced="loadKline"
    />

    <!-- 日K主图指标设置弹窗 -->
    <KlineIndicatorDialog
      v-model="showKlineIndicatorDialog"
      :settings="klineIndicatorSettings"
      @confirm="confirmKlineIndicatorDialog"
    />

    <!-- 股票评估弹窗 -->
    <StockEvalDialog
      v-model="showEvalDialog"
      :stock="stock"
      :loading="evalLoading"
      :scores="evalScores"
      @evaluate="handleEvaluate"
    />

    <StockChatAssistant
      :tsCode="props.tsCode"
      :stock="stock"
      @survey-saved="surveyListRef?.reload()"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { stockApi, watchlistApi } from '@/api'
import { ElMessage } from 'element-plus'
import { useKlineAdjust, KLINE_LOAD_DAYS } from '@/composables/useKlineAdjust'
import { useKlineIndicatorSettings } from '@/composables/useKlineIndicatorSettings'
import { useStockDetailKeyboardNav } from '@/composables/useStockDetailKeyboardNav'
import FollowStockDialog from '@/components/FollowStockDialog.vue'
import StockChatAssistant from '@/components/StockChatAssistant.vue'
import StockDetailHeader from '@/components/stock-detail/StockDetailHeader.vue'
import StockNotesDialog from '@/components/stock-detail/StockNotesDialog.vue'
import SwitchGroupDialog from '@/components/stock-detail/SwitchGroupDialog.vue'
import StockTagsDialog from '@/components/stock-detail/StockTagsDialog.vue'
import StockSettingsDialog from '@/components/stock-detail/StockSettingsDialog.vue'
import KlineIndicatorDialog from '@/components/stock-detail/KlineIndicatorDialog.vue'
import StockEvalDialog from '@/components/stock-detail/StockEvalDialog.vue'
import StockSignalTimeline from '@/components/stock-detail/StockSignalTimeline.vue'
import StockSurveyList from '@/components/stock-detail/StockSurveyList.vue'
import StockFinancials from '@/components/stock-detail/StockFinancials.vue'
import StockChipDistribution from '@/components/stock-detail/StockChipDistribution.vue'
import StockMoneyflowChart from '@/components/stock-detail/StockMoneyflowChart.vue'
import StockConcepts from '@/components/stock-detail/StockConcepts.vue'
import StockMainKline from '@/components/stock-detail/StockMainKline.vue'
import StockTagsSection from '@/components/stock-detail/StockTagsSection.vue'
import StockWatchlistInfo from '@/components/stock-detail/StockWatchlistInfo.vue'
import StockInfoSection from '@/components/stock-detail/StockInfoSection.vue'
import StockIndicatorGuide from '@/components/stock-detail/StockIndicatorGuide.vue'

const props = defineProps(['tsCode'])

const stock = ref(null)
const klineData = ref([])
const buySignalsData = ref([])
const weeklyKlineData = ref([])

// 子区块组件引用
const signalTimelineRef = ref(null)
const surveyListRef = ref(null)
const chipDistRef = ref(null)

// 股票备注弹窗
const showNotesDialog = ref(false)

// 所属分组相关
const watchlistStockInfo = ref(null)
const showSwitchGroupDialog = ref(false)

// 标签相关
const stockTags = ref([])
const tagPopoverVisible = ref(false)

// 关注弹窗相关
const followDialogVisible = ref(false)
const currentFollowStock = ref(null)
const isWatched = ref(false)

const showSettingsDialog = ref(false)

// 股票评估
const showEvalDialog = ref(false)
const evalLoading = ref(false)
const evalScores = ref([])

// K线图上仅显示评分 > 85 的高分日期
const highEvalScores = computed(() =>
  evalScores.value.filter(s => s.score != null && s.score > 85)
)

// K线复权与指标设置（复权计算/常量见 composables/useKlineAdjust.js）
const { adjType, adjustedKlineData, indicatorKlineData, adjustedWeeklyKlineData } =
  useKlineAdjust(klineData, weeklyKlineData)

const { klineIndicatorSettings, saveKlineIndicatorSettings } = useKlineIndicatorSettings()

// 日K主图指标设置弹窗
const showKlineIndicatorDialog = ref(false)

const openKlineIndicatorDialog = () => {
  showKlineIndicatorDialog.value = true
}

const confirmKlineIndicatorDialog = (newSettings) => {
  saveKlineIndicatorSettings(newSettings)
}

// 成交量较前一交易日涨幅（K线数据为时间升序，最后一条为最新）
const volumeChangePct = computed(() => {
  const data = adjustedKlineData.value
  if (!data || data.length < 2) return null
  const current = data[data.length - 1]?.volume
  const prev = data[data.length - 2]?.volume
  if (!current || !prev || prev === 0) return null
  return ((current - prev) / prev) * 100
})

const volumeTooltipText = computed(() => {
  const pct = volumeChangePct.value
  if (pct == null) return '较昨日: --'
  const sign = pct > 0 ? '+' : ''
  return `较昨日: ${sign}${pct.toFixed(2)}%`
})

onMounted(() => {
  loadStockDetail()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const handleResize = () => {
  chipDistRef.value?.resize()
}

const loadStockDetail = async () => {
  try {
    const response = await stockApi.getDetail(props.tsCode)
    stock.value = response.data
    if (stock.value?.name) {
      document.title = stock.value.name
    }

    await loadKline()
    await loadBuySignals()
    await loadWatchlistStockInfo()
    await loadTags()
    await loadEvalScores()
  } catch (error) {
    console.error('Failed to load stock detail:', error)
    ElMessage.error('加载失败')
  }
}

const loadKline = async () => {
  try {
    // 日线请求 180 天：保证 MA60 等指标在可见范围内能正确计算
    const dailyResponse = await stockApi.getKline(props.tsCode, 'daily', KLINE_LOAD_DAYS)
    klineData.value = dailyResponse.data.data || []
  } catch (error) {
    console.error('Failed to load daily kline:', error)
  }
  try {
    const weeklyResponse = await stockApi.getWeeklyKline(props.tsCode, 60)
    weeklyKlineData.value = weeklyResponse.data || []
  } catch (error) {
    console.error('Failed to load weekly kline:', error)
  }
}

const loadBuySignals = async () => {
  try {
    const response = await stockApi.getBuySignals(props.tsCode, 3)
    if (response.success) {
      buySignalsData.value = response.data?.signals || []
    }
  } catch (error) {
    console.error('Failed to load buy signals:', error)
  }
}

// 关注股票
const openFollowDialog = () => {
  if (!stock.value) return
  currentFollowStock.value = stock.value
  followDialogVisible.value = true
}

const handleFollowSuccess = () => {
  followDialogVisible.value = false
  isWatched.value = true
  loadWatchlistStockInfo()
}

// 加载股票所属分组信息
const loadWatchlistStockInfo = async () => {
  try {
    const response = await watchlistApi.getStockByTsCode(props.tsCode)
    if (response.success && response.data) {
      watchlistStockInfo.value = response.data
      isWatched.value = true
    } else {
      watchlistStockInfo.value = null
      isWatched.value = false
    }
  } catch (error) {
    watchlistStockInfo.value = null
    isWatched.value = false
  }
}

// 加载股票标签
const loadTags = async () => {
  try {
    const response = await stockApi.getTags(props.tsCode)
    if (response.success) {
      stockTags.value = response.data?.tags || []
    }
  } catch (error) {
    console.error('Failed to load tags:', error)
  }
}

// 打开标签编辑弹窗
const openTagPopover = () => {
  tagPopoverVisible.value = true
}

// 标签保存成功后更新本地标签并追加 ADD_TAG 信号
const onTagsSaved = ({ selectedTags, signal }) => {
  stockTags.value = selectedTags
  if (signal) {
    signalTimelineRef.value?.addSignal(signal)
  }
}

// 打开切换分组弹窗
const openSwitchGroupDialog = () => {
  showSwitchGroupDialog.value = true
}

// 打开股票备注弹窗
const openNotesDialog = () => {
  showNotesDialog.value = true
}

// 备注保存成功后追加 NOTE 信号并同步分组备注
const onNotesSaved = ({ signal, notes }) => {
  signalTimelineRef.value?.addSignal(signal)
  if (watchlistStockInfo.value) {
    watchlistStockInfo.value.notes = notes
  }
}

// 键盘快捷键（Ctrl+X 序列，见 composables/useStockDetailKeyboardNav.js）
useStockDetailKeyboardNav({
  stock,
  showNotesDialog,
  tagPopoverVisible,
  openNotesDialog,
  openTagPopover
})

// 打开股票评估弹窗
const openEvalDialog = () => {
  showEvalDialog.value = true
}

// 执行股票评估
const handleEvaluate = async (date) => {
  if (!stock.value?.ts_code) return
  evalLoading.value = true
  try {
    const response = await stockApi.evaluateStock(stock.value.ts_code, date)
    if (response.success) {
      ElMessage.success('评估完成')
      // 直接从响应获取评分数据，弹窗保持打开显示结果
      if (response.scores) {
        evalScores.value = response.scores
      } else {
        await loadEvalScores()
      }
    } else {
      ElMessage.error(response.error || '评估失败')
    }
  } catch (error) {
    console.error('Failed to evaluate stock:', error)
    ElMessage.error('评估请求失败')
  } finally {
    evalLoading.value = false
  }
}

// 加载缓存的评估分数（页面加载时调用）
const loadEvalScores = async () => {
  if (!stock.value?.ts_code) return
  try {
    const response = await stockApi.getEvalScores(stock.value.ts_code)
    if (response.success && response.data?.scores) {
      evalScores.value = response.data.scores
    } else {
      evalScores.value = []
    }
  } catch (error) {
    // 无缓存数据时静默失败
    evalScores.value = []
  }
}
</script>

<style scoped>
.stock-detail {
  padding: 20px;
}
</style>
