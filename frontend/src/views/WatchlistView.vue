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
        <el-radio-group v-model="showAllStocks" size="small" style="margin-right: 10px;">
          <el-radio-button :label="false">仅热点</el-radio-button>
          <el-radio-button :label="true">全部</el-radio-button>
        </el-radio-group>
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

    <el-row :gutter="20" v-if="currentWatchlist && filteredStocks.length">
      <el-col 
        :xs="24" :sm="12" :md="8" :lg="6" 
        v-for="stock in filteredStocks" 
        :key="stock.id"
        class="stock-card-col"
      >
        <el-card class="stock-card" shadow="hover">
          <div class="stock-header">
            <div class="stock-info">
              <div class="stock-title">
                <h3>{{ stock.name || stock.symbol }}</h3>
                <el-tag
                  :type="stock.status === 2 ? 'info' : 'danger'"
                  size="small"
                  class="status-tag"
                  effect="light"
                >
                  {{ stock.status === 2 ? '静默' : '热点' }}
                </el-tag>
                <el-button
                  type="success"
                  size="small"
                  circle
                  @click="openSwitchGroupDialog(stock)"
                  title="切换分组"
                >
                  <el-icon><Switch /></el-icon>
                </el-button>
              </div>
              <span class="stock-code">{{ stock.ts_code }}</span>
            </div>

          </div>

          <div class="stock-price" v-if="stockPrices[stock.ts_code]">
            <div class="current-price">
              ¥{{ stockPrices[stock.ts_code].price?.toFixed(2) }}
            </div>
            <div 
              class="change-pct"
              :class="getChangeClass(stockPrices[stock.ts_code].change_pct)"
            >
              {{ stockPrices[stock.ts_code].change_pct > 0 ? '+' : '' }}
              {{ stockPrices[stock.ts_code].change_pct?.toFixed(2) }}%
            </div>
          </div>

          <div class="stock-price" v-if="stockPrices[stock.ts_code]">
            <div v-if="stockPrices[stock.ts_code].market_cap">
              {{ formatMarketCap(stockPrices[stock.ts_code].market_cap) }}
            </div>
          </div>

          
          <div class="stock-signal" v-if="stockSignals[stock.ts_code]">
            <el-tag 
              :type="getSignalType(stockSignals[stock.ts_code].signal_type)"
              size="small"
              class="signal-tag"
            >
              {{ formatSignal(stockSignals[stock.ts_code].signal_type) }}
            </el-tag>
            <span class="signal-strength" v-if="stockSignals[stock.ts_code].signal_strength">
              强度: {{ stockSignals[stock.ts_code].signal_strength }}/5
            </span>
          </div>

          <div class="stock-notes" v-if="stock.notes">
            <el-text type="info" size="small">{{ stock.notes }}</el-text>
          </div>

          <div class="stock-watch-reason" v-if="stock.watch_reason">
            <el-tag type="warning" size="small" effect="plain">
              {{ stock.watch_reason }}
            </el-tag>
          </div>

          <div class="stock-tags">
            <el-popover
              :width="280"
              trigger="click"
              v-model:visible="tagPopoverVisible[stock.id]"
              @show="popoverSelectedTags = [...(stock.tags || [])]"
            >
              <template #reference>
                <div class="tags-display" v-if="stock.tags && stock.tags.length">
                  <el-tag
                    v-for="tag in stock.tags"
                    :key="tag"
                    size="small"
                    effect="plain"
                    class="stock-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
                <el-tag v-else size="small" effect="plain" type="info" class="stock-tag-add">+ 标签</el-tag>
              </template>
              <div class="tag-edit-content">
                <el-select
                  v-model="popoverSelectedTags"
                  multiple
                  filterable
                  allow-create
                  placeholder="选择或输入标签"
                  style="width: 100%"
                >
                  <el-option
                    v-for="tag in allTags"
                    :key="tag"
                    :label="tag"
                    :value="tag"
                  />
                </el-select>
                <div class="tag-edit-actions">
                  <el-button size="small" @click="tagPopoverVisible[stock.id] = false">取消</el-button>
                  <el-button size="small" type="primary" @click="saveStockTags(stock)">保存</el-button>
                </div>
              </div>
            </el-popover>
          </div>

          <div class="stock-footer">
            <span class="added-time">{{ formatDate(stock.added_at) }}</span>
            
            <el-button
              type="primary"
              size="small"
              link
              @click="openNotesDialog(stock)"
            >
              备注
            </el-button>

            <el-button
              type="primary"
              size="small"
              link
              @click="openXueqiu(stock.ts_code)"
            >
              雪球
            </el-button>

            <el-button
              type="primary"
              size="small"
              text
              @click="$router.push(`/stock/${stock.ts_code}`)"
            >
              详情
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

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
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useWatchlistStore } from '@/stores/watchlist'
import { watchlistApi, stockApi, signalApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Refresh, Switch, Camera } from '@element-plus/icons-vue'
import { useWebSocket } from '@/composables/useWebSocket'

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
const showAllStocks = ref(false)  // false = 只显示热点股票, true = 显示全部
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

let priceRefreshInterval = null
const { onMessageType, offMessageType } = useWebSocket()

const handleNotesUpdated = ({ ts_code, notes }) => {
  if (!currentWatchlist.value?.stocks) return
  const stock = currentWatchlist.value.stocks.find(s => s.ts_code === ts_code)
  if (stock) {
    stock.notes = notes
  }
}

const filteredStocks = computed(() => {
  if (!currentWatchlist.value?.stocks) return []
  let stocks = currentWatchlist.value.stocks
  
  // 筛选热点/全部
  if (!showAllStocks.value) {
    stocks = stocks.filter(stock => stock.status === 1 || !stock.status)
  }
  
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
})

// 监听路由参数变化，当切换到不同的 watchlist 时重新加载
watch(() => props.id, (newId, oldId) => {
  if (newId !== oldId) {
    selectedDate.value = ''
    selectedWatchReason.value = ''
    selectedTags.value = []
    loadWatchlist()
  }
})

onUnmounted(() => {
  if (priceRefreshInterval) {
    clearInterval(priceRefreshInterval)
  }
  offMessageType('notes_updated', handleNotesUpdated)
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
  if (!change) return ''
  return change > 0 ? 'up' : change < 0 ? 'down' : ''
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
  if (cap >= 100000000) {
    return (cap / 100000000).toFixed(2) + '亿'
  }
  if (cap >= 10000) {
    return (cap / 10000).toFixed(2) + '万'
  }
  return cap.toString()
}

const openXueqiu = (tsCode) => {
  // 转换格式: 300006.SZ -> SZ300006
  const [code, exchange] = tsCode.split('.')
  const xueqiuCode = exchange + code
  window.open(`https://xueqiu.com/S/${xueqiuCode}`, '_blank')
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

// 保存股票标签
const saveStockTags = async (stock) => {
  try {
    await watchlistApi.updateStockTags(stock.ts_code, popoverSelectedTags.value)
    stock.tags = [...popoverSelectedTags.value]
    ElMessage.success('标签更新成功')
    tagPopoverVisible.value[stock.id] = false
  } catch (error) {
    console.error('Failed to update stock tags:', error)
    ElMessage.error('标签更新失败')
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

.stock-card-col {
  margin-bottom: 20px;
}

.stock-card {
  height: 100%;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.stock-info h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
}

.stock-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-tag {
  font-size: 11px;
}

.stock-code {
  color: #909399;
  font-size: 12px;
}

.stock-price {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 15px;
}

.current-price {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.change-pct {
  font-size: 16px;
  font-weight: 500;
}

.change-pct.up {
  color: #f56c6c;
}

.change-pct.down {
  color: #67c23a;
}

.market-cap {
  margin-left: auto;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.stock-signal {
  margin-bottom: 15px;
}

.signal-tag {
  margin-right: 10px;
}

.signal-strength {
  color: #606266;
  font-size: 12px;
}

.stock-notes {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.stock-watch-reason {
  margin-bottom: 15px;
}

.stock-tags {
  margin-bottom: 15px;
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

.stock-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.added-time {
  color: #909399;
  font-size: 12px;
}

.stock-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-option-code {
  color: #909399;
  font-size: 12px;
}

.stock-kline-actions {
  margin-bottom: 15px;
}

.input-hint {
  margin-top: 10px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}
</style>
