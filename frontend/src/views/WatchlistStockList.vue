<template>
  <div class="page-container">

    <el-card class="filter-card">
      <div class="filter-layout">
        <div class="filter-left">
          <el-form :inline="true">
            <el-form-item label="搜索">
              <el-input
                v-model="filter.search"
                placeholder="ts_code / 股票名称"
                clearable
                style="width: 200px"
                @keyup.enter="handleFilterChange"
                @clear="handleFilterChange"
              />
            </el-form-item>
            <el-form-item label="板块">
              <el-select
                v-model="filter.industries"
                placeholder="选择板块"
                multiple
                filterable
                clearable
                collapse-tags
                collapse-tags-tooltip
                style="width: 200px"
                @change="handleFilterChange"
              >
                <el-option
                  v-for="item in industryOptions"
                  :key="item.name"
                  :label="`${item.name} (${item.count})`"
                  :value="item.name"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="分组">
              <el-select
                v-model="filter.watchlist_id"
                placeholder="选择分组"
                clearable
                style="width: 160px"
                @change="handleFilterChange"
              >
                <el-option
                  v-for="wl in watchlistOptions"
                  :key="wl.id"
                  :label="wl.name"
                  :value="wl.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="标签">
              <el-select
                v-model="filter.tags"
                placeholder="选择标签"
                multiple
                filterable
                clearable
                collapse-tags
                collapse-tags-tooltip
                style="width: 200px"
                @change="handleFilterChange"
              >
                <el-option
                  v-for="tag in allTags"
                  :key="tag"
                  :label="tag"
                  :value="tag"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="涨幅">
              <el-slider
                v-model="filter.change_pct_range"
                range
                :min="-20"
                :max="20"
                :step="1"
                :marks="{ '-20': '-20%', '0': '0%', '20': '20%' }"
                style="width: 200px"
                @change="handleFilterChange"
              />
            </el-form-item>
            <el-form-item label="市场">
              <el-radio-group v-model="filter.market_type" @change="handleFilterChange">
                <el-radio-button label="主板" value="main" />
                <el-radio-button label="创业" value="chye" />
                <el-radio-button label="科创" value="kcb" />
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleFilterChange">搜索</el-button>
              <el-button @click="resetFilter">重置</el-button>
              <el-button @click="copyAllTsCodes">拷贝</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div class="filter-right">
          <span class="stat-up">{{ stockStats.up }}</span>
          <span class="stat-separator">/</span>
          <span class="stat-down">{{ stockStats.down }}</span>
        </div>
      </div>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="tableData" stripe border @sort-change="handleSortChange" @row-click="handleRowClick" :row-class-name="tableRowClassName">
        <el-table-column prop="ts_code" label="TS代码" width="130" fixed="left">
          <template #default="{ row }">
            <a :href="`/stock/${row.ts_code}`" target="_blank" rel="noopener" style="color: var(--el-color-primary); text-decoration: none;">
              {{ row.ts_code }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="股票名称" width="120" fixed="left" />
        <el-table-column prop="industry" label="板块" width="140">
          <template #header>
            <div class="industry-col-header">
              <span>板块</span>
              <el-popover
                v-model:visible="industryFilterVisible"
                placement="bottom-start"
                :width="280"
                trigger="click"
                :show-arrow="false"
                popper-class="industry-filter-popper"
              >
                <template #reference>
                  <el-badge :is-dot="filter.industries.length > 0" class="industry-filter-badge">
                    <el-icon
                      class="industry-filter-icon"
                      :class="{ active: filter.industries.length > 0 }"
                    >
                      <Filter />
                    </el-icon>
                  </el-badge>
                </template>

                <div class="industry-filter-panel">
                  <div class="filter-panel-header">
                    <span class="filter-panel-title">板块筛选</span>
                    <span class="filter-panel-count">
                      已选 {{ tempIndustries.length }} / {{ industryOptions.length }}
                    </span>
                  </div>
                  <el-input
                    v-model="industrySearch"
                    placeholder="搜索板块名称"
                    clearable
                    size="small"
                    class="filter-panel-search"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                  <div class="filter-panel-options">
                    <el-checkbox-group v-model="tempIndustries">
                      <el-checkbox
                        v-for="item in filteredIndustryOptions"
                        :key="item.name"
                        :value="item.name"
                        class="filter-panel-option"
                      >
                        <span class="option-name">{{ item.name }}</span>
                        <span class="option-count">{{ item.count }}</span>
                      </el-checkbox>
                    </el-checkbox-group>
                    <el-empty
                      v-if="filteredIndustryOptions.length === 0"
                      :image-size="40"
                      description="无匹配板块"
                    />
                  </div>
                  <div class="filter-panel-actions">
                    <el-button size="small" @click="clearIndustryFilter">清空</el-button>
                    <el-button size="small" type="primary" @click="applyIndustryFilter">确定</el-button>
                  </div>
                </div>
              </el-popover>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="close_price" label="最新收盘价" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.close_price !== null">
              {{ row.close_price.toFixed(2) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="change_pct"
          label="最新涨幅"
          width="120"
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span v-if="row.change_pct !== null" :class="getChangeClass(row.change_pct)">
              {{ row.change_pct >= 0 ? '+' : '' }}{{ row.change_pct.toFixed(2) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_mv" label="最新市值" width="140" align="right">
          <template #default="{ row }">
            <span v-if="row.total_mv !== null">
              {{ formatMarketCap(row.total_mv) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="备注" min-width="180">
          <template #default="{ row }">
            <el-popover
              v-if="row.notes"
              placement="top"
              :width="300"
              trigger="hover"
              :show-after="300"
            >
              <template #reference>
                <span class="notes-cell">{{ row.notes }}</span>
              </template>
              <div class="notes-popover-content">{{ row.notes }}</div>
            </el-popover>
            <span v-else class="notes-cell">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">
            <span>{{ formatDateTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="watchlist_name" label="所属分组" min-width="140" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="openStockDetail(row.ts_code)">
              详情
            </el-button>
            <el-button type="primary" size="small" link @click="openNotesDialog(row)">
              备注
            </el-button>
            <el-button type="primary" size="small" link @click="openSwitchGroupDialog(row)">
              换组
            </el-button>
            <el-button type="primary" size="small" link @click="openXueqiu(row.ts_code)">
              雪球
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 30, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 股票备注弹窗 -->
    <el-dialog v-model="showNotesDialog" title="编辑股票备注" width="500px">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ selectedStockForNotes?.name }} ({{ selectedStockForNotes?.ts_code }})</el-text>
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
          <el-text>{{ selectedStockForSwitch?.name }} ({{ selectedStockForSwitch?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="目标分组" required>
          <el-select
            v-model="selectedTargetWatchlist"
            placeholder="选择目标分组"
            style="width: 100%"
          >
            <el-option
              v-for="wl in availableWatchlistsForSwitch"
              :key="wl.id"
              :label="wl.name"
              :value="wl.id"
              :disabled="wl.id === selectedStockForSwitch?.watchlist_id"
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Filter, Search } from '@element-plus/icons-vue'
import { watchlistApi } from '@/api'
import { useWebSocket } from '@/composables/useWebSocket'
import { getChangeClass, openXueqiu } from '@/utils/stock'

const loading = ref(false)
const tableData = ref([])
const stockStats = ref({ up: 0, down: 0 })
const industryOptions = ref([])
const watchlistOptions = ref([])
const allTags = ref([])

const filter = reactive({
  search: '',
  industries: [],
  watchlist_id: null,
  tags: [],
  market_type: 'chye',
  change_pct_range: [-20, 20]
})

// 板块列头筛选浮窗
const industryFilterVisible = ref(false)
const industrySearch = ref('')
// 临时选择缓冲：打开浮窗时从 filter.industries 同步，确定时才写回并请求
const tempIndustries = ref([])

watch(industryFilterVisible, (visible) => {
  if (visible) {
    tempIndustries.value = [...filter.industries]
    industrySearch.value = ''
  }
})

// 板块筛选可选项（按搜索词过滤）
const filteredIndustryOptions = computed(() => {
  if (!industrySearch.value) return industryOptions.value
  const q = industrySearch.value.toLowerCase()
  return industryOptions.value.filter(opt => opt.name.toLowerCase().includes(q))
})



const pagination = reactive({
  page: 1,
  page_size: 30,
  total: 0,
  total_pages: 0
})

const sortState = reactive({
  sort_by_change_pct: null
})

// 行选中相关
const selectedRowId = ref(null)

// 股票备注相关
const showNotesDialog = ref(false)
const selectedStockForNotes = ref(null)
const stockNotesInput = ref('')
const notesLoading = ref(false)

// 切换分组相关
const showSwitchGroupDialog = ref(false)
const selectedStockForSwitch = ref(null)
const selectedTargetWatchlist = ref(null)
const switchGroupReason = ref('')
const switchLoading = ref(false)
const availableWatchlistsForSwitch = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const res = await watchlistApi.getAllWatchlistStocks({
      page: pagination.page,
      page_size: pagination.page_size,
      search: filter.search || null,
      industry: filter.industries.length > 0 ? filter.industries.join(',') : null,
      watchlist_id: filter.watchlist_id || null,
      tags: filter.tags,
      sort_by_change_pct: sortState.sort_by_change_pct,
      market_type: filter.market_type || null,
      change_pct_min: filter.change_pct_range[0],
      change_pct_max: filter.change_pct_range[1]
    })
    if (res.success) {
      tableData.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total
        pagination.total_pages = res.pagination.total_pages
      }
      stockStats.value = res.stats || { up: 0, down: 0 }
    } else {
      ElMessage.error(res.error || '获取数据失败')
    }
  } catch (err) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const fetchOptions = async () => {
  try {
    const [industriesRes, watchlistRes, tagsRes] = await Promise.all([
      watchlistApi.getIndustries(),
      watchlistApi.getAll(),
      watchlistApi.getAllTags()
    ])
    if (industriesRes.success) {
      industryOptions.value = industriesRes.data || []
    }
    if (watchlistRes.success) {
      watchlistOptions.value = watchlistRes.data || []
    }
    if (tagsRes.success) {
      allTags.value = tagsRes.data.tags || []
    }
  } catch (err) {
    console.error('Failed to fetch options:', err)
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  fetchData()
}

// 板块列头浮窗：确定 / 清空（操作 tempIndustries，确定时写回 filter）
const applyIndustryFilter = () => {
  filter.industries = [...tempIndustries.value]
  industryFilterVisible.value = false
  handleFilterChange()
}

const clearIndustryFilter = () => {
  tempIndustries.value = []
}

const resetFilter = () => {
  filter.search = ''
  filter.industries = []
  filter.watchlist_id = null
  filter.tags = []
  filter.market_type = 'chye'
  filter.change_pct_range = [-20, 20]
  industrySearch.value = ''
  sortState.sort_by_change_pct = null
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

const handleSortChange = ({ prop, order }) => {
  if (prop === 'change_pct') {
    if (order === 'ascending') {
      sortState.sort_by_change_pct = 'asc'
    } else if (order === 'descending') {
      sortState.sort_by_change_pct = 'desc'
    } else {
      sortState.sort_by_change_pct = null
    }
  } else {
    sortState.sort_by_change_pct = null
  }
  pagination.page = 1
  fetchData()
}

const handleRowClick = (row) => {
  selectedRowId.value = row.id
}

const tableRowClassName = ({ row }) => {
  if (row.id === selectedRowId.value) {
    return 'selected-row'
  }
  return ''
}

const openStockDetail = (tsCode) => {
  if (!tsCode) return
  window.open(`/stock/${tsCode}`, '_blank')
}

// 复制当前页所有 ts_code 到剪贴板
const copyAllTsCodes = async () => {
  const codes = tableData.value.map(row => row.ts_code).filter(Boolean)
  if (codes.length === 0) {
    ElMessage.warning('没有可复制的 TS 代码')
    return
  }
  try {
    await navigator.clipboard.writeText(codes.join('\n'))
    ElMessage.success(`已复制 ${codes.length} 条 TS 代码`)
  } catch (err) {
    console.error('Failed to copy ts_codes:', err)
    ElMessage.error('复制失败，请手动复制')
  }
}

const formatMarketCap = (value) => {
  if (!value) return '-'
  if (value >= 100000000) {
    return (value / 100000000).toFixed(2) + '亿'
  }
  if (value >= 10000) {
    return (value / 10000).toFixed(2) + '万'
  }
  return value.toFixed(0)
}

const formatDateTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}`
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

    const stock = tableData.value.find(
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

// 打开切换分组弹窗
const openSwitchGroupDialog = async (stock) => {
  selectedStockForSwitch.value = stock
  selectedTargetWatchlist.value = null
  switchGroupReason.value = ''
  showSwitchGroupDialog.value = true
  availableWatchlistsForSwitch.value = watchlistOptions.value
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
    // 刷新列表
    fetchData()
  } catch (error) {
    console.error('Failed to switch stock group:', error)
    ElMessage.error('切换分组失败')
  } finally {
    switchLoading.value = false
  }
}

const { onMessageType, offMessageType } = useWebSocket()

const handleNotesUpdated = ({ ts_code, notes }) => {
  const stock = tableData.value.find(s => s.ts_code === ts_code)
  if (stock) {
    stock.notes = notes
  }
}

onMounted(() => {
  fetchOptions()
  fetchData()
  onMessageType('notes_updated', handleNotesUpdated)
})

onUnmounted(() => {
  offMessageType('notes_updated', handleNotesUpdated)
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
}
.filter-card {
  margin-bottom: 20px;
}
.filter-layout {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.filter-left {
  flex: 0 0 80%;
}
.filter-right {
  flex: 0 0 20%;
  text-align: right;
  font-size: 18px;
  font-weight: bold;
}
.stat-up {
  color: var(--stock-up);
}
.stat-down {
  color: var(--stock-down);
}
.stat-separator {
  color: var(--text-muted);
  margin: 0 4px;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.up {
  color: var(--stock-up);
}
.down {
  color: var(--stock-down);
}
.flat {
  color: var(--text-muted);
}
.notes-cell {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}
.notes-popover-content {
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
  font-size: 13px;
  color: var(--text-primary);
}

:deep(.el-table .selected-row > td.el-table__cell) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table .el-table__fixed .selected-row > td.el-table__cell) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table .el-table__fixed-right .selected-row > td.el-table__cell) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: var(--bg-active) !important;
}

:deep(.el-table .el-table__fixed .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: var(--bg-active) !important;
}

:deep(.el-table .el-table__fixed-right .el-table__body tr.selected-row:hover > td.el-table__cell) {
  background-color: var(--bg-active) !important;
}

/* 板块列头筛选 */
.industry-col-header {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.industry-filter-badge {
  display: inline-flex;
  align-items: center;
}
.industry-filter-icon {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 14px;
  transition: color 0.2s;
}
.industry-filter-icon:hover,
.industry-filter-icon.active {
  color: var(--el-color-primary);
}

/* 浮窗面板（通过 popper-class 跨出 scoped 作用域） */
.industry-filter-popper.el-popover.el-popper {
  padding: 12px !important;
}
.industry-filter-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.filter-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.filter-panel-title {
  font-weight: 600;
  color: var(--text-primary);
}
.filter-panel-count {
  font-size: 12px;
  color: var(--text-muted);
}
.filter-panel-search {
  width: 100%;
}
.filter-panel-options {
  max-height: 280px;
  overflow-y: auto;
  border-top: 1px solid var(--el-border-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 6px 4px;
}
.filter-panel-options .el-checkbox {
  display: flex;
  align-items: center;
  height: 28px;
  margin-right: 0;
  width: 100%;
}
.filter-panel-options .el-checkbox .el-checkbox__label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 4px;
}
.filter-panel-option .option-name {
  color: var(--text-primary);
}
.filter-panel-option .option-count {
  color: var(--text-muted);
  font-size: 12px;
  margin-left: 8px;
}
.filter-panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
