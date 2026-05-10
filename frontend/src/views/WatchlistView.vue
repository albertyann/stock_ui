<template>
  <div class="watchlist-view">
    <div class="header-actions" v-if="currentWatchlist">
      <h2>{{ currentWatchlist.watchlist_name }}</h2>
      <div class="header-right">
        <el-select
          v-model="selectedDate"
          placeholder="选择日期筛选"
          clearable
          style="width: 150px; margin-right: 10px;"
          @change="handleDateChange"
        >
          <el-option
            v-for="date in availableDates"
            :key="date"
            :label="formatDate(date)"
            :value="date"
          />
        </el-select>
        <el-select
          v-model="selectedWatchReason"
          placeholder="关注原因"
          clearable
          style="width: 130px; margin-right: 10px;"
          @change="handleWatchReasonChange"
        >
          <el-option
            v-for="reason in availableWatchReasons"
            :key="reason.value"
            :label="reason.label"
            :value="reason.value"
          />
        </el-select>
        <el-select
          v-model="selectedTags"
          multiple
          filterable
          clearable
          placeholder="标签筛选"
          style="width: 150px; margin-right: 10px;"
        >
          <el-option
            v-for="tag in allTags"
            :key="tag"
            :label="tag"
            :value="tag"
          />
        </el-select>
        <el-button v-if="props.id == 2" type="warning" @click="handleSnapshot" :loading="snapshotLoading">
          <el-icon><Camera /></el-icon>快照
        </el-button>
        <el-button v-if="props.id == 2" @click="openSnapshotHistory">
          快照历史
        </el-button>
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>添加股票
        </el-button>
      </div>
    </div>
    
    <div class="header-actions" v-else-if="loading">
      <h2>加载中...</h2>
    </div>
    
    <div class="header-actions" v-else>
      <h2>加载失败</h2>
      <el-button type="primary" @click="loadWatchlist(selectedDate)">
        <el-icon><Refresh /></el-icon>重新加载
      </el-button>
    </div>

    <el-empty v-if="currentWatchlist && !filteredStocks.length" :description="selectedDate ? '所选日期暂无信号数据' : '暂无股票，点击上方按钮添加'" />

    <div v-if="currentWatchlist && filteredStocks.length" class="stock-list">
      <div
        v-for="(stock, index) in filteredStocks"
        :key="stock.id"
        class="stock-card"
        :class="[getChangeClass(stockPrices[stock.ts_code]?.change_pct), { selected: index === selectedStockIndex }]"
      >
        <!-- 左侧：股票信息 -->
        <div class="stock-info-section">
          <div class="stock-header">
            <div class="stock-title">
              <div class="stock-name">{{ stock.name || stock.symbol }}</div>
              <div class="stock-code">{{ stock.ts_code }}</div>
              <el-tag
                :type="stock.status === 2 ? 'info' : 'danger'"
                size="small"
                class="status-tag"
                effect="light"
              >
                {{ stock.status === 2 ? '静默' : '热点' }}
              </el-tag>
            </div>
            <div
              class="change-badge"
              :class="getChangeClass(stockPrices[stock.ts_code]?.change_pct)"
            >
              {{ stockPrices[stock.ts_code] ? formatChange(stockPrices[stock.ts_code].change_pct) : '0.00%' }}
            </div>
          </div>

          <div class="stock-body">
            <!-- 当前价格 -->
            <div class="price-section">
              <div
                class="current-price"
                :class="getChangeClass(stockPrices[stock.ts_code]?.change_pct)"
              >
                ¥{{ stockPrices[stock.ts_code]?.price?.toFixed(2) || '-' }}
              </div>
              <div class="change-info">
                <span :class="getChangeClass(stockPrices[stock.ts_code]?.change_pct)">
                  {{ stockPrices[stock.ts_code] ? (stockPrices[stock.ts_code].change_pct > 0 ? '+' : '') + stockPrices[stock.ts_code].change_pct?.toFixed(2) + '%' : '0.00%' }}
                </span>
              </div>
            </div>

            <!-- 市值信息 -->
            <div class="volume-section">
              <div class="volume-row">
                <span class="label">市值</span>
                <span class="value">{{ formatMarketCap(stockPrices[stock.ts_code]?.market_cap) }}</span>
              </div>
            </div>

            <!-- 信号信息 -->
            <div class="signal-section" v-if="stockSignals[stock.ts_code]">
              <div class="signal-row">
                <span class="label">信号</span>
                <el-tag
                  :type="getSignalType(stockSignals[stock.ts_code].signal_type)"
                  size="small"
                >
                  {{ formatSignal(stockSignals[stock.ts_code].signal_type) }}
                </el-tag>
                <span
                  class="signal-strength"
                  v-if="stockSignals[stock.ts_code].signal_strength"
                >
                  强度: {{ stockSignals[stock.ts_code].signal_strength }}/5
                </span>
              </div>
            </div>

            <!-- 添加时间 -->
            <div class="time-section">
              <span class="time-label">添加时间：</span>
              <span class="time-value">{{ formatDate(stock.added_at) }}</span>
            </div>
          </div>

          <div class="stock-footer">
            <el-button
              size="small"
              type="primary"
              link
              @click="openSwitchGroupDialog(stock)"
            >
              换组
            </el-button>
            <el-button
              size="small"
              type="primary"
              link
              @click="openNotesDialog(stock)"
            >
              备注
            </el-button>
            <el-button
              size="small"
              type="primary"
              link
              @click="openXueqiu(stock.ts_code)"
            >
              雪球
            </el-button>
            <el-button
              size="small"
              type="primary"
              link
              @click="openStockDetail(stock.ts_code)"
            >
              详情
            </el-button>
          </div>

        </div>

        <!-- 右侧：K线图 -->
        <div class="stock-chart-section">
          <StockKlineChart
            :ref="(el) => { if (el) chartRefs.set(stock.ts_code, el) }"
            :ts-code="stock.ts_code"
            :kline-data="klineDataCache.get(stock.ts_code) || []"
            :show-m-a-c-d="true"
            min-height="260px"
          />
        </div>
      </div>
    </div>

    <el-dialog v-model="showAddDialog" title="批量添加股票" width="500px">
      <el-input
        v-model="stockInputText"
        type="textarea"
        :rows="6"
        placeholder="输入股票代码，每行一个或用逗号分隔&#10;例如：&#10;000001.SZ&#10;600000.SH, 000002.SZ"
        resize="none"
      />
      <div class="input-hint">
        <el-text type="info" size="small">
          支持格式：每行一个代码，或用逗号分隔。代码格式如 000001.SZ、600000.SH
        </el-text>
      </div>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addStocks" :disabled="!stockInputText.trim() || addLoading" :loading="addLoading">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 股票备注弹窗 -->
    <el-dialog v-model="showNotesDialog" title="编辑股票备注" width="500px">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ selectedStockForNotes?.name || selectedStockForNotes?.symbol }} ({{ selectedStockForNotes?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="stockNotesInput"
            type="textarea"
            :rows="4"
            placeholder="请输入股票备注信息..."
            resize="none"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showNotesDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveStockNotes"
          :disabled="notesLoading"
          :loading="notesLoading"
        >
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 切换分组弹窗 -->
    <el-dialog v-model="showSwitchGroupDialog" title="切换分组" width="500px">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ selectedStockForSwitch?.name || selectedStockForSwitch?.symbol }}</el-text>
        </el-form-item>
        <el-form-item label="目标分组" required>
          <el-select
            v-model="selectedTargetWatchlist"
            placeholder="选择目标分组"
            style="width: 100%"
          >
            <el-option
              v-for="watchlist in availableWatchlists"
              :key="watchlist.id"
              :label="watchlist.name"
              :value="watchlist.id"
              :disabled="watchlist.id === Number(props.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="变更理由" required>
          <el-input
            v-model="switchGroupReason"
            type="textarea"
            :rows="3"
            placeholder="请填写变更理由（必填）"
            resize="none"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showSwitchGroupDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="switchStockGroup" 
          :disabled="!selectedTargetWatchlist || !switchGroupReason.trim() || switchLoading"
          :loading="switchLoading"
        >
          确认切换
        </el-button>
      </template>
    </el-dialog>

    <!-- 快照历史弹窗 -->
    <el-dialog v-model="showSnapshotHistoryDialog" title="快照历史" width="900px">
      <el-table :data="snapshots" style="width: 100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <el-table :data="row.items" :border="true" size="small" style="margin: 10px;">
              <el-table-column prop="ts_code" label="股票代码" width="120" />
              <el-table-column prop="name" label="股票名称" width="120" />
              <el-table-column prop="industry" label="板块" width="120" />
              <el-table-column prop="notes" label="备注" show-overflow-tooltip />
            </el-table>
          </template>
        </el-table-column>
        <el-table-column prop="snapshot_date" label="快照日期" width="120" />
        <el-table-column prop="snapshot_time" label="快照时间" width="120" />
        <el-table-column prop="items.length" label="股票数量" width="100">
          <template #default="{ row }">
            {{ row.items?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="showSnapshotHistoryDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useWatchlistStore } from '@/stores/watchlist'
import { watchlistApi, stockApi, signalApi, realtimeApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Refresh, Switch, Camera } from '@element-plus/icons-vue'
import { useWebSocket } from '@/composables/useWebSocket'
import StockKlineChart from '@/components/StockKlineChart.vue'

const route = useRoute()
const store = useWatchlistStore()

const props = defineProps(['id'])

const currentWatchlist = ref(null)
const stockPrices = ref({})
const stockSignals = ref({})
const showAddDialog = ref(false)
const stockInputText = ref('')
const addLoading = ref(false)
const loading = ref(false)
const selectedDate = ref('')
const availableDates = ref([])
const selectedWatchReason = ref('')  // 选中的关注原因
const availableWatchReasons = ref([])  // 可用的关注原因列表
const selectedTags = ref([])  // 选中的标签筛选

// 切换分组相关
const showSwitchGroupDialog = ref(false)
const selectedStockForSwitch = ref(null)
const selectedTargetWatchlist = ref(null)
const switchGroupReason = ref('')
const switchLoading = ref(false)
const availableWatchlists = ref([])

// 股票备注相关
const showNotesDialog = ref(false)
const selectedStockForNotes = ref(null)
const stockNotesInput = ref('')
const notesLoading = ref(false)
// 标签相关
const allTags = ref([])
const tagPopoverVisible = ref({})
const popoverSelectedTags = ref([])

// 快照相关
const snapshotLoading = ref(false)
const showSnapshotHistoryDialog = ref(false)
const snapshots = ref([])

// K线图相关
const klineDataCache = ref(new Map())
const chartRefs = ref(new Map())

// 选中股票索引（用于键盘导航）
const selectedStockIndex = ref(0)

// Ctrl+x 前缀键状态
const ctrlXPressed = ref(false)

let priceRefreshInterval = null
const { onMessageType, offMessageType } = useWebSocket()

const handleNotesUpdated = ({ ts_code, notes }) => {
  if (!currentWatchlist.value?.stocks) return
  const stock = currentWatchlist.value.stocks.find(s => s.ts_code === ts_code)
  if (stock) {
    stock.notes = notes
  }
}

// 键盘事件处理
const handleKeydown = (event) => {
  // 如果焦点在输入框或文本框中，不处理快捷键
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.isContentEditable) {
    return
  }

  const maxIndex = filteredStocks.value.length - 1

  // 处理 Ctrl+x 前缀键
  if (event.ctrlKey && event.key === 'x') {
    event.preventDefault()
    ctrlXPressed.value = true
    return
  }

  // 处理 Ctrl+x 后的子命令
  if (ctrlXPressed.value) {
    ctrlXPressed.value = false

    if (event.key === 'o') {
      // Ctrl+x+o: 打开雪球
      event.preventDefault()
      const selectedStock = filteredStocks.value[selectedStockIndex.value]
      if (selectedStock) {
        openXueqiu(selectedStock.ts_code)
      }
      return
    }
  }

  // j/k 导航
  if (event.key === 'j') {
    event.preventDefault()
    if (selectedStockIndex.value < maxIndex) {
      selectedStockIndex.value++
      scrollToSelectedStock()
    }
  } else if (event.key === 'k') {
    event.preventDefault()
    if (selectedStockIndex.value > 0) {
      selectedStockIndex.value--
      scrollToSelectedStock()
    }
  }
}

// 滚动到选中的股票（居中显示）
const scrollToSelectedStock = () => {
  nextTick(() => {
    const stockCards = document.querySelectorAll('.stock-card')
    if (stockCards[selectedStockIndex.value]) {
      stockCards[selectedStockIndex.value].scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

const filteredStocks = computed(() => {
  if (!currentWatchlist.value?.stocks) return []
  let stocks = currentWatchlist.value.stocks
  
  // 筛选关注原因
  if (selectedWatchReason.value) {
    stocks = stocks.filter(stock => stock.watch_reason === selectedWatchReason.value)
  }
  
  // 筛选标签 (OR逻辑)
  if (selectedTags.value.length > 0) {
    stocks = stocks.filter(stock => 
      stock.tags?.some(tag => selectedTags.value.includes(tag))
    )
  }
  
  return stocks
})

onMounted(async () => {
  await loadLastTradingDay()
  await loadWatchlist(selectedDate.value || null)
  await loadAllTags()
  onMessageType('notes_updated', handleNotesUpdated)
  // 注册键盘事件监听
  window.addEventListener('keydown', handleKeydown)
})

// 监听路由参数变化，当切换到不同的 watchlist 时重新加载
watch(() => props.id, (newId, oldId) => {
  if (newId !== oldId) {
    selectedDate.value = ''
    selectedWatchReason.value = ''
    selectedTags.value = []
    selectedStockIndex.value = 0
    loadWatchlist()
  }
})

// 筛选条件变化时重置选中索引
watch([selectedWatchReason, selectedTags], () => {
  selectedStockIndex.value = 0
})

onUnmounted(() => {
  if (priceRefreshInterval) {
    clearInterval(priceRefreshInterval)
  }
  offMessageType('notes_updated', handleNotesUpdated)
  // 注销键盘事件监听
  window.removeEventListener('keydown', handleKeydown)
})

const loadLastTradingDay = async () => {
  try {
    const response = await watchlistApi.getLastTradingDay(props.id)
    if (response.data?.last_trading_day) {
      selectedDate.value = response.data.last_trading_day
    }
  } catch (error) {
    console.error('Failed to load last trading day:', error)
  }
}

const loadWatchlist = async (watchDate = null) => {
  loading.value = true
  selectedStockIndex.value = 0
  try {
    const response = await watchlistApi.getStocksByWatchDate(
      props.id, 
      watchDate, 
      watchDate ? null : 20
    )
    currentWatchlist.value = response.data
    
    if (currentWatchlist.value?.stocks?.length > 0) {
      await loadPrices()
      await loadSignals()
      // 加载K线数据
      nextTick(() => {
        currentWatchlist.value.stocks.forEach(stock => {
          fetchKlineData(stock.ts_code)
        })
      })
    }
    
    await loadAvailableDates()
    await loadAvailableWatchReasons()
  } catch (error) {
    console.error('Failed to load watchlist:', error)
    ElMessage.error('加载失败')
    currentWatchlist.value = null
  } finally {
    loading.value = false
  }
}

const loadPrices = async () => {
  for (const stock of currentWatchlist.value.stocks) {
    try {
      const response = await stockApi.getDetail(stock.ts_code)
      if (response.data) {
        stockPrices.value[stock.ts_code] = {
          price: response.data.current_price,
          change_pct: response.data.change_pct,
          volume: response.data.volume,
          market_cap: response.data.market_cap
        }
      }
    } catch (error) {
      console.error(`Failed to load price for ${stock.ts_code}:`, error)
    }
  }
}

const fetchKlineData = async (tsCode) => {
  if (klineDataCache.value.has(tsCode)) return

  try {
    const response = await realtimeApi.getKline(tsCode, 'daily', 180)
    if (response.success && response.data && response.data.data) {
      klineDataCache.value.set(tsCode, response.data.data)
    }
  } catch (error) {
    console.error('Failed to load kline for', tsCode, error)
  }
}

const loadSignals = async () => {
  for (const stock of currentWatchlist.value.stocks) {
    try {
      const response = await signalApi.getLatest(stock.ts_code)
      if (response.data) {
        stockSignals.value[stock.ts_code] = response.data
      }
    } catch (error) {
      console.error(`Failed to load signal for ${stock.ts_code}:`, error)
    }
  }
}

const loadAvailableDates = async () => {
  try {
    // 使用 getWatchDates 获取 watch_date 日期列表（而不是 signal_date）
    const response = await watchlistApi.getWatchDates(props.id)
    if (response.data) {
      availableDates.value = response.data.dates || []
    }
  } catch (error) {
    console.error('Failed to load available dates:', error)
  }
}

const handleDateChange = (date) => {
  selectedDate.value = date
  loadWatchlist(date)
}

const handleWatchReasonChange = (reason) => {
  selectedWatchReason.value = reason
}

const loadAvailableWatchReasons = async () => {
  try {
    const response = await watchlistApi.getWatchReasons(props.id)
    if (response.data?.watch_reasons) {
      availableWatchReasons.value = response.data.watch_reasons
    }
  } catch (error) {
    console.error('Failed to load available watch reasons:', error)
  }
}

const loadAllTags = async () => {
  try {
    const response = await watchlistApi.getAllTags()
    if (response.data) {
      allTags.value = response.data
    }
  } catch (error) {
    console.error('Failed to load all tags:', error)
  }
}

const parseStockCodes = (input) => {
  const codes = input
    .split(/[\n,;，；\s]+/)
    .map(code => code.trim())
    .filter(code => code.length > 0)
  
  return [...new Set(codes)]
}

const addStocks = async () => {
  const codes = parseStockCodes(stockInputText.value)
  if (codes.length === 0) return
  
  addLoading.value = true
  const results = { success: [], failed: [] }
  
  try {
    // 顺序添加，避免并发问题
    for (const tsCode of codes) {
      try {
        await watchlistApi.addStock(props.id, { ts_code: tsCode })
        results.success.push(tsCode)
      } catch (error) {
        console.error(`Failed to add stock ${tsCode}:`, error)
        results.failed.push(tsCode)
      }
    }
    
    // 显示结果
    if (results.success.length > 0 && results.failed.length === 0) {
      ElMessage.success(`成功添加 ${results.success.length} 只股票`)
    } else if (results.success.length > 0 && results.failed.length > 0) {
      ElMessage.warning(`添加完成：成功 ${results.success.length} 只，失败 ${results.failed.length} 只`)
    } else {
      ElMessage.error('添加失败，请检查股票代码格式')
    }
    
    // 关闭对话框并重置
    showAddDialog.value = false
    stockInputText.value = ''
    
    // 刷新列表
    if (results.success.length > 0) {
      await loadWatchlist(selectedDate.value)
    }
  } catch (error) {
    console.error('Failed to add stocks:', error)
    ElMessage.error('添加过程中发生错误')
  } finally {
    addLoading.value = false
  }
}

const setStockCalm = async (stock) => {
  try {
    await watchlistApi.updateStockStatus(props.id, stock.id, 2)
    ElMessage.success(`已将 ${stock.name || stock.symbol} 设为冷静状态`)
    await loadWatchlist(selectedDate.value)
  } catch (error) {
    console.error('Failed to set stock calm:', error)
    ElMessage.error('设置冷静状态失败')
  }
}

// 打开切换分组弹窗
const openSwitchGroupDialog = async (stock) => {
  selectedStockForSwitch.value = stock
  selectedTargetWatchlist.value = null
  switchGroupReason.value = ''
  showSwitchGroupDialog.value = true
  
  // 加载可用的分组列表
  try {
    const response = await watchlistApi.getAll()
    if (response.data) {
      availableWatchlists.value = response.data
    }
  } catch (error) {
    console.error('Failed to load watchlists:', error)
    ElMessage.error('加载分组列表失败')
  }
}

// 切换股票分组
const switchStockGroup = async () => {
  if (!selectedStockForSwitch.value || !selectedTargetWatchlist.value) return
  if (!switchGroupReason.value.trim()) {
    ElMessage.warning('请填写变更理由')
    return
  }
  
  switchLoading.value = true
  try {
    await watchlistApi.moveStockToWatchlist(
      selectedStockForSwitch.value.id,
      selectedTargetWatchlist.value,
      switchGroupReason.value.trim()
    )
    ElMessage.success('切换分组成功')
    showSwitchGroupDialog.value = false
    // 从当前列表中移除已切换的股票卡片
    if (currentWatchlist.value?.stocks) {
      currentWatchlist.value.stocks = currentWatchlist.value.stocks.filter(
        stock => stock.id !== selectedStockForSwitch.value.id
      )
    }
  } catch (error) {
    console.error('Failed to switch stock group:', error)
    ElMessage.error('切换分组失败')
  } finally {
    switchLoading.value = false
  }
}

const getChangeClass = (change) => {
  if (!change) return 'flat'
  return change > 0 ? 'up' : change < 0 ? 'down' : 'flat'
}

const formatChange = (changePct) => {
  if (!changePct) return '0.00%'
  if (changePct > 0) return `+${changePct.toFixed(2)}%`
  if (changePct < 0) return `${changePct.toFixed(2)}%`
  return '0.00%'
}

const getSignalType = (type) => {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'info', NOTE: 'warning' }
  return map[type] || 'info'
}

const formatSignal = (type) => {
  const map = { BUY: '买入', SELL: '卖出', WATCH: '观望', NOTE: '备注' }
  return map[type] || type
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatMarketCap = (cap) => {
  if (!cap) return ''
  // total_mv from stock_service.getDetail is in 万元, 10000万 = 1亿
  return (cap / 10000).toFixed(2) + '亿'
}

const openXueqiu = (tsCode) => {
  // 转换格式: 300006.SZ -> SZ300006
  const [code, exchange] = tsCode.split('.')
  const xueqiuCode = exchange + code
  window.open(`https://xueqiu.com/S/${xueqiuCode}`, '_blank')
}

const openStockDetail = (tsCode) => {
  const url = window.location.origin + `/stock/${tsCode}`
  window.open(url, '_blank')
}

// 打开股票备注弹窗
const openNotesDialog = (stock) => {
  selectedStockForNotes.value = stock
  stockNotesInput.value = stock.notes || ''
  showNotesDialog.value = true
}

// 保存股票备注
const saveStockNotes = async () => {
  if (!selectedStockForNotes.value) return

  notesLoading.value = true
  try {
    await watchlistApi.updateStockNotes(
      selectedStockForNotes.value.id,
      stockNotesInput.value.trim()
    )
    ElMessage.success('备注更新成功')
    showNotesDialog.value = false

    const stock = currentWatchlist.value?.stocks?.find(
      s => s.id === selectedStockForNotes.value.id
    )
    if (stock) {
      stock.notes = stockNotesInput.value.trim()
    }
  } catch (error) {
    console.error('Failed to update stock notes:', error)
    ElMessage.error('备注更新失败')
  } finally {
    notesLoading.value = false
  }
}


const handleSnapshot = async () => {
  if (!currentWatchlist.value?.stocks?.length) {
    ElMessage.warning('当前分组没有股票，无法创建快照')
    return
  }

  const stocksToSnapshot = filteredStocks.value.map(stock => ({
    ts_code: stock.ts_code,
    name: stock.name || stock.symbol,
    industry: stock.industry || '',
    notes: stock.notes || ''
  }))

  if (stocksToSnapshot.length === 0) {
    ElMessage.warning('当前筛选条件下没有股票，无法创建快照')
    return
  }

  snapshotLoading.value = true
  try {
    await watchlistApi.createSnapshot(props.id, stocksToSnapshot)
    ElMessage.success(`成功创建快照，共 ${stocksToSnapshot.length} 只股票`)
  } catch (error) {
    console.error('Failed to create snapshot:', error)
    ElMessage.error('快照创建失败')
  } finally {
    snapshotLoading.value = false
  }
}

const openSnapshotHistory = async () => {
  showSnapshotHistoryDialog.value = true
  await loadSnapshots()
}

const loadSnapshots = async () => {
  try {
    const response = await watchlistApi.getSnapshots(props.id)
    snapshots.value = response.data || []
  } catch (error) {
    console.error('Failed to load snapshots:', error)
    ElMessage.error('加载快照历史失败')
  }
}
</script>

<style scoped>
.watchlist-view {
  padding: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions h2 {
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

/* 股票列表 - 纵向排列 */
.stock-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 股票卡片 - 横向布局 */
.stock-card {
  display: flex;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 2px solid transparent;
  overflow: hidden;
  transition: all 0.3s ease;
}

.stock-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stock-card.up {
  border-color: #f56c6c;
}

.stock-card.down {
  border-color: #67c23a;
}

.stock-card.flat {
  border-color: #dcdfe6;
}

.stock-card.selected {
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.3);
  border-color: #409eff !important;
  transform: translateY(-2px);
  position: relative;
}

.stock-card.selected::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #409eff 0%, #66b1ff 100%);
  border-radius: 12px 0 0 12px;
}

/* 左侧信息区域 */
.stock-info-section {
  flex: 0 0 320px;
  padding: 20px;
  background: #fafbfc;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.stock-title {
  flex: 1;
}

.stock-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stock-code {
  font-size: 13px;
  color: #909399;
}

.status-tag {
  margin-top: 6px;
  font-size: 11px;
}

.change-badge {
  width: 72px;
  height: 36px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.change-badge.up {
  background: linear-gradient(135deg, #f56c6c 0%, #ff8c8c 100%);
}

.change-badge.down {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.change-badge.flat {
  background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
}

.stock-body {
  flex: 1;
}

.price-section {
  text-align: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.current-price {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 6px;
}

.current-price.up {
  color: #f56c6c;
}

.current-price.down {
  color: #67c23a;
}

.current-price.flat {
  color: #909399;
}

.change-info {
  font-size: 13px;
}

.change-info .up {
  color: #f56c6c;
}

.change-info .down {
  color: #67c23a;
}

.change-info .flat {
  color: #909399;
}

.volume-section {
  margin-bottom: 12px;
}

.volume-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.volume-row:last-child {
  margin-bottom: 0;
}

.volume-row .label {
  font-size: 12px;
  color: #909399;
}

.volume-row .value {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.signal-section {
  margin-bottom: 12px;
}

.signal-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.signal-row .label {
  font-size: 12px;
  color: #909399;
}

.signal-strength {
  font-size: 12px;
  color: #606266;
}

.watch-reason-section {
  margin-bottom: 12px;
}

.reason-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.reason-row .label {
  font-size: 12px;
  color: #909399;
}

.time-section {
  font-size: 11px;
  color: #909399;
  text-align: center;
  margin-bottom: 12px;
}

.time-label {
  margin-right: 4px;
}

.stock-footer {
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stock-tags {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.tags-display {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.stock-tag {
  cursor: pointer;
}

.stock-tag-add {
  cursor: pointer;
}

.tag-edit-content {
  padding: 5px 0;
}

.tag-edit-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.input-hint {
  margin-top: 10px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

/* 右侧图表区域 */
.stock-chart-section {
  flex: 1;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  min-height: 280px;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .stock-info-section {
    flex: 0 0 280px;
  }
}

@media (max-width: 992px) {
  .stock-card {
    flex-direction: column;
  }

  .stock-info-section {
    flex: none;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #ebeef5;
  }

  .stock-chart-section {
    min-height: 260px;
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .watchlist-view {
    padding: 12px;
  }

  .header-actions {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .header-right {
    flex-wrap: wrap;
    gap: 10px;
  }

  .stock-info-section {
    padding: 16px;
  }

  .stock-chart-section {
    padding: 12px;
  }

  .current-price {
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .stock-header {
    flex-direction: column;
    gap: 10px;
  }

  .change-badge {
    width: 100%;
    height: 32px;
  }

  .stock-footer {
    justify-content: center;
  }
}
</style>
