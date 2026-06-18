<template>
  <div>
    <div class="stock-detail" v-if="stock">
      <el-page-header @back="$router.back()" :content="`${stock.name}(${stock.ts_code})${stock.industry ? ' - ' + stock.industry : ''}`" />

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
              <span class="metric-label">成交量</span>
              <span class="metric-value">{{ formatVolume(stock.volume) }}</span>
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
            <el-button size="small" :type="isWatched ? 'info' : 'warning'" link @click="openFollowDialog" :disabled="isWatched">
              {{ isWatched ? '已关注' : '关注' }}
            </el-button>
            <el-button size="small" type="primary" link @click="openXueqiu(stock)">
              雪球
            </el-button>
            <el-button size="small" link @click="showSettingsDialog = true">
              <el-icon><Setting /></el-icon>
            </el-button>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20" class="mt-20">
        <el-col :span="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>日线</span>
                <div class="kline-header-right">
                  <span class="signal-legend" v-if="buySignalsData.length > 0">
                    <span class="legend-item">
                      <span class="legend-dot" style="background-color:#e6a23c;border-radius:50%;"></span>MA25回踩
                    </span>
                    <span class="legend-item">
                      <span class="legend-dot legend-diamond"></span>MA10回踩
                    </span>
                    <span class="legend-item">
                      <span class="legend-dot legend-tri"></span>RSI12强势
                    </span>
                    <span class="legend-item">
                      <span class="legend-dot legend-rect"></span>双命中
                    </span>
                  </span>
                  <el-radio-group v-model="adjType" size="small" class="adj-type-selector">
                    <el-radio-button value="forward">前复权</el-radio-button>
                    <el-radio-button value="backward">后复权</el-radio-button>
                    <el-radio-button value="none">不复权</el-radio-button>
                  </el-radio-group>
                </div>
              </div>
            </template>
            
            <!-- POC: 日 K 改用 KLineChart 渲染 (周 K 仍为 ECharts, 便于同页对比) -->
            <StockKlineChartKLC
              ref="klineChartRef"
              :tsCode="props.tsCode"
              :klineData="adjustedKlineData"
              :buySignals="buySignalsData"
              height="360px"
            />
          </el-card>

          <!-- 指标 -->
          <el-card class="mt-20">
            <template #header>
              <div class="card-header">
                <span>指标</span>
                <span class="volume-legend">
                  <span class="legend-item"><span class="dot" style="background-color:#f56c6c;"></span>阳线</span>
                  <span class="legend-item"><span class="dot" style="background-color:#67c23a;"></span>阴线</span>
                  <span class="legend-item"><span class="dot" style="background-color:#e6a23c;"></span>MA5量</span>
                </span>
              </div>
            </template>
            <StockRsiChart
              ref="rsiChartRef"
              :klineData="adjustedKlineData"
            />
            <StockVolumeChart
              ref="volumeChartRef"
              :klineData="adjustedKlineData"
            />
            <StockMacdChart
              ref="macdChartRef"
              :klineData="adjustedKlineData"
            />
            <StockAdxChart
              ref="adxChartRef"
              :klineData="adjustedKlineData"
            />
            
          </el-card>

          <!-- 信号时间线 -->
          <el-card class="mt-20 signal-timeline-card" v-loading="signalsLoading">
            <template #header>
              <div class="card-header">
                <span>信号记录</span>
                <div class="header-actions">
                  <span class="signal-count" v-if="signalList.length > 0">共 {{ signalList.length }} 条</span>
                  <el-button size="small" type="primary" link @click="openNotesDialog">
                    <el-icon><EditPen /></el-icon>备注
                  </el-button>
                </div>
              </div>
            </template>

            <div v-if="signalList.length === 0" class="empty-signals">
              <el-empty description="暂无信号记录" :image-size="60" />
            </div>

            <el-timeline v-else>
              <el-timeline-item
                v-for="signal in signalList"
                :key="signal.id"
                :type="getSignalTimelineType(signal.signal_type)"
                :timestamp="formatDateTime(signal.created_at || signal.signal_date)"
                placement="top"
              >
                <div class="signal-timeline-content">
                  <div class="signal-timeline-header">
                    <el-tag size="small" :type="getSignalType(signal.signal_type)">
                      {{ formatSignal(signal.signal_type) }}
                    </el-tag>
                    <span v-if="signal.signal_strength" class="signal-strength">
                      强度: {{ signal.signal_strength }}
                    </span>
                  </div>

                  <!-- NOTE 类型展示 note_content -->
                  <div v-if="signal.signal_type === 'NOTE'" class="signal-note">
                    {{ signal.note_content || '无内容' }}
                  </div>

                  <!-- ADD_TAG 类型展示标签列表 -->
                  <div v-else-if="signal.signal_type === 'ADD_TAG'" class="signal-tags">
                    <el-tag
                      v-for="tag in (signal.note_content || '').split(', ')"
                      :key="tag"
                      size="small"
                      effect="plain"
                    >
                      {{ tag }}
                    </el-tag>
                  </div>

                  <!-- 其他类型展示 execution_result -->
                  <div v-else class="signal-result">
                    <div v-if="signal.execution_result" class="result-text">
                      {{ signal.execution_result }}
                    </div>
                    <div v-else class="result-empty">
                      信号产生时价格: ¥{{ signal.current_price?.toFixed(2) || '-' }}
                    </div>
                  </div>

                  <div v-if="signal.indicators" class="signal-indicators-mini">
                    <el-tag size="small" type="info" v-if="signal.indicators.ma20">
                      MA20: {{ signal.indicators.ma20.toFixed(2) }}
                    </el-tag>
                    <el-tag size="small" type="info" v-if="signal.indicators.macd">
                      MACD: {{ signal.indicators.macd.toFixed(2) }}
                    </el-tag>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-card>

          <!-- AI 调研记录 -->
          <el-card class="mt-20 stock-survey-card" v-loading="surveysLoading">
            <template #header>
              <div class="card-header">
                <span>AI 调研记录</span>
                <span class="signal-count" v-if="surveyList.length > 0">共 {{ surveyList.length }} 条</span>
              </div>
            </template>

            <div v-if="surveyList.length === 0" class="empty-signals">
              <el-empty description="暂无 AI 调研记录" :image-size="60" />
            </div>

            <el-timeline v-else>
              <el-timeline-item
                v-for="survey in surveyList"
                :key="survey.id"
                type="primary"
                :timestamp="formatDateTime(survey.created_at)"
                placement="top"
              >
                <div class="survey-timeline-content">
                  <div v-if="survey.query" class="survey-query">
                    问题：{{ survey.query }}
                  </div>
                  <div class="survey-result" v-html="renderSurveyContent(survey.content)"></div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>

        <el-col :span="8">
          <!-- 周线K线图 -->
          <el-card class="weekly-kline-card">
            <template #header>
              <div class="card-header">
                <span>周线</span>
              </div>
            </template>
            <StockKlineChart
              ref="weeklyKlineChartRef"
              :tsCode="props.tsCode"
              :klineData="adjustedWeeklyKlineData"
              height="360px"
              :maPeriods="[5, 10]"
            />
          </el-card>

          <!-- 审计意见 -->
          <el-card v-if="auditList.length > 0" class="audit-card mt-20">
            <template #header>
              <div class="card-header">
                <span>审计意见</span>
              </div>
            </template>
            <div class="audit-list">
              <div v-for="item in auditList" :key="item.end_date" class="audit-item">
                <div class="audit-item__header">
                  <span class="audit-item__period">{{ formatEndDate(item.end_date) }}</span>
                  <el-tag
                    size="small"
                    :type="getAuditTagType(item.audit_result)"
                    effect="plain"
                  >
                    {{ item.audit_result || '-' }}
                  </el-tag>
                </div>
                <div class="audit-item__agency" v-if="item.audit_agency">
                  {{ item.audit_agency }}
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="mt-20" v-loading="moneyflowLoading">
            <template #header>
              <div class="card-header">
                <span>资金流向</span>
                <div class="moneyflow-legend">
                  <el-checkbox v-model="showLargeOnly" size="small">仅大单</el-checkbox>
                  <span class="legend-item"><span class="dot red"></span>正向</span>
                  <span class="legend-item"><span class="dot green"></span>负向</span>
                </div>
              </div>
            </template>
            <div class="moneyflow-summary" v-if="moneyflowSummary">
              <div class="summary-item">
                <span class="summary-label">20日净流入</span>
                <span class="summary-value" :class="moneyflowSummary.d20 >= 0 ? 'up' : 'down'">
                  {{ formatNetInflow(moneyflowSummary.d20) }}
                </span>
              </div>
              <div class="summary-item">
                <span class="summary-label">10日净流入</span>
                <span class="summary-value" :class="moneyflowSummary.d10 >= 0 ? 'up' : 'down'">
                  {{ formatNetInflow(moneyflowSummary.d10) }}
                </span>
              </div>
              <div class="summary-item">
                <span class="summary-label">5日净流入</span>
                <span class="summary-value" :class="moneyflowSummary.d5 >= 0 ? 'up' : 'down'">
                  {{ formatNetInflow(moneyflowSummary.d5) }}
                </span>
              </div>
            </div>
            <div ref="moneyflowChart" style="height: 300px;"></div>
          </el-card>

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

          <!-- 标签管理 -->
          <el-card class="mt-20">
            <template #header>
              <div class="card-header">
                <span>标签</span>
                <el-button size="small" type="primary" link @click="openTagPopover">
                  <el-icon><EditPen /></el-icon>编辑
                </el-button>
              </div>
            </template>

            <div class="tags-display">
              <template v-if="stockTags.length > 0">
                <el-tag
                  v-for="tag in stockTags"
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

          <!-- 筹码分布 -->
          <el-card class="mt-20" v-loading="chipLoading">
            <template #header>
              <div class="card-header">
                <span>筹码分布</span>
                <el-date-picker
                  v-model="selectedChipDate"
                  type="date"
                  placeholder="选择日期"
                  size="small"
                  style="width: 140px"
                  value-format="YYYY-MM-DD"
                  @change="onChipDateChange"
                />
              </div>
            </template>
            <div v-if="chipData.chips && chipData.chips.length > 0">
              <div class="chip-summary" v-if="chipConcentration !== null">
                <div class="summary-item">
                  <span class="summary-label">筹码集中度</span>
                  <span class="summary-value">{{ chipConcentration.toFixed(2) }}%</span>
                </div>
              </div>
              <StockChipChart
                ref="chipChartRef"
                :chipData="chipData.chips"
                :currentPrice="chipData.current_price"
                height="280px"
              />
            </div>
            <el-empty v-else description="暂无筹码数据" :image-size="60" />
          </el-card>

          <el-card class="mt-20" v-if="watchlistStockInfo">
            <template #header>
              <div class="card-header">
                <span>所属分组</span>
                <el-button size="small" type="primary" link @click="openSwitchGroupDialog">
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

          <el-card class="mt-20">
            <template #header>
              <div class="card-header">
                <span>股票信息</span>
                <el-button size="small" type="primary" link @click="openCreateInfoDialog">
                  添加
                </el-button>
              </div>
            </template>

            <div class="stock-infos-list">
              <template v-if="stockInfos.length > 0">
                <div
                  v-for="info in stockInfos"
                  :key="info.id"
                  class="stock-info-item"
                >
                  <div class="info-content">{{ info.memo }}</div>
                  <div class="info-actions">
                    <el-button
                      size="small"
                      type="primary"
                      link
                      @click="openEditInfoDialog(info)"
                    >
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      link
                      @click="deleteStockInfo(info.id)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </template>
              <el-text v-else type="info" size="small">暂无信息</el-text>
            </div>
          </el-card>

          <el-card class="mt-20 indicator-guide-card">
            <template #header>
              <div class="card-header">
                <span>指标说明</span>
                <el-tag type="success" size="small">真突破（可关注）</el-tag>
              </div>
            </template>

            <div class="indicator-guide">
              <div class="guide-feature">
                均线多头，MACD金叉，大单流入，OBV新高，ADX走强
              </div>

              <div class="guide-section">
                <div class="guide-title">MA (5,10,20)</div>
                <div class="guide-text">5&gt;10&gt;20，股价沿5日线攀升。</div>
              </div>

              <div class="guide-section">
                <div class="guide-title">MACD</div>
                <div class="guide-text">DIF上穿DEA，红柱渐长，在零轴上方二次金叉。</div>
              </div>

              <div class="guide-section">
                <div class="guide-title">大单/DDX</div>
                <div class="guide-text">连续3日大单净流入，DDX红柱逐日放大（非脉冲）。</div>
              </div>

              <div class="guide-section">
                <div class="guide-title">OBV</div>
                <div class="guide-text">随股价创新高，OBV同步创120日新高。</div>
              </div>

              <div class="guide-section">
                <div class="guide-title">ADX</div>
                <div class="guide-text">从20升至35，+DI在-DI上方。</div>
              </div>

              <el-divider />

              <div class="guide-summary">
                <div class="summary-line">
                  <span class="summary-label">综合判断：</span>强趋势+资金健康+量价配合。
                </div>
                <div class="summary-line">
                  <span class="summary-label">操作：</span>沿5日线持有，ADX&gt;50且走平考虑减仓。
                </div>
              </div>
            </div>
          </el-card>

        </el-col>
      </el-row>
    </div>

    <el-empty v-else description="加载中..." />

    <!-- 编辑备注弹窗 -->
    <el-dialog v-model="showNotesDialog" title="编辑股票备注" width="500px" @opened="onNotesDialogOpened">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            ref="notesInputRef"
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
          <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="当前分组">
          <el-text>{{ watchlistStockInfo?.watchlist_name }}</el-text>
        </el-form-item>
        <el-form-item label="目标分组" required>
          <el-select
            v-model="selectedTargetWatchlist"
            placeholder="选择目标分组"
            style="width: 100%"
          >
            <el-option
              v-for="wl in availableWatchlists"
              :key="wl.id"
              :label="wl.name"
              :value="wl.id"
              :disabled="wl.id === watchlistStockInfo?.watchlist_id"
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

    <!-- 编辑标签弹窗 -->
    <el-dialog v-model="tagPopoverVisible" title="编辑标签" width="500px">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="已选标签">
          <div class="selected-tags-container">
            <el-tag
              v-for="tag in popoverSelectedTags"
              :key="tag"
              closable
              size="small"
              @close="removeSelectedTag(tag)"
              class="selected-tag"
            >
              {{ tag }}
            </el-tag>
            <el-input
              ref="tagInputRef"
              v-model="newTagInput"
              size="small"
              class="tag-input"
              placeholder="输入新标签，回车添加"
              @keydown.enter.prevent="addNewTag"
            />
          </div>
        </el-form-item>
        <el-form-item label="可选标签">
          <div class="available-tags-container">
            <el-tag
              v-for="tag in availableTagsList"
              :key="tag"
              size="small"
              effect="plain"
              class="available-tag"
              @click="addSelectedTag(tag)"
            >
              {{ tag }}
            </el-tag>
            <el-text v-if="availableTagsList.length === 0" type="info" size="small">
              暂无可选标签
            </el-text>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="tagPopoverVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveStockTags"
        >
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 股票信息弹窗 -->
    <el-dialog v-model="showInfoDialog" :title="infoDialogMode === 'create' ? '添加信息' : '编辑信息'" width="500px">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="信息内容">
          <el-input
            v-model="infoMemoInput"
            type="textarea"
            :rows="4"
            placeholder="请输入股票相关信息..."
            resize="none"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showInfoDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveStockInfo"
          :disabled="infoLoading"
          :loading="infoLoading"
        >
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 关注股票弹窗 -->
    <FollowStockDialog
      v-model="followDialogVisible"
      :stock="currentFollowStock"
      @success="handleFollowSuccess"
    />

    <!-- 设置弹窗 -->
    <el-dialog v-model="showSettingsDialog" title="设置" width="500px">
      <el-form label-width="100px">
        <el-form-item label="股票">
          <el-text>{{ stock?.name }} ({{ stock?.ts_code }})</el-text>
        </el-form-item>
        <el-form-item label="数据同步">
          <div class="sync-kline-section">
            <div class="sync-kline-desc">
              删除当前股票已有K线数据，从2018年至今全量重新拉取日线数据。
            </div>
            <el-button
              type="danger"
              :loading="syncKlineLoading"
              :disabled="syncKlineLoading"
              @click="handleSyncKline"
            >
              同步K线数据
            </el-button>
            <div v-if="syncKlineResult" class="sync-result" :class="syncKlineResult.success ? 'sync-success' : 'sync-error'">
              {{ syncKlineResult.success
                ? `同步完成：删除日线 ${syncKlineResult.deleted_daily || 0} 条，周线 ${syncKlineResult.deleted_weekly || 0} 条`
                : `同步失败：${syncKlineResult.error}`
              }}
            </div>
          </div>
        </el-form-item>
        <el-form-item label="删除股票">
          <div class="delete-stock-section">
            <div class="delete-stock-desc">
              将当前股票从关注列表中移除。
            </div>
            <el-button
              type="danger"
              :loading="deleteStockLoading"
              :disabled="deleteStockLoading || !watchlistStockInfo"
              @click="handleDeleteStock"
            >
              删除股票
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showSettingsDialog = false">关闭</el-button>
      </template>
    </el-dialog>
    <StockChatAssistant
      :tsCode="props.tsCode"
      :stock="stock"
      @survey-saved="loadSurveys"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from '@/utils/echarts'
import { stockApi, signalApi, basicDataApi, watchlistApi, stockInfoApi, sectorApi, aiChatApi } from '@/api'
import { ElMessage } from 'element-plus'
import { EditPen, Plus, Edit, Delete, Setting } from '@element-plus/icons-vue'
import StockKlineChart from '@/components/StockKlineChart.vue'
import StockKlineChartKLC from '@/components/StockKlineChartKLC.vue'
import StockAdxChart from '@/components/StockAdxChart.vue'
import StockVolumeChart from '@/components/StockVolumeChart.vue'
import StockMacdChart from '@/components/StockMacdChart.vue'
import StockRsiChart from '@/components/StockRsiChart.vue'
import StockChipChart from '@/components/StockChipChart.vue'
import FollowStockDialog from '@/components/FollowStockDialog.vue'
import StockChatAssistant from '@/components/StockChatAssistant.vue'

const props = defineProps(['tsCode'])

const stock = ref(null)
const klineData = ref([])
const buySignalsData = ref([])
const weeklyKlineData = ref([])
const latestSignal = ref(null)
const klineChartRef = ref(null)
const weeklyKlineChartRef = ref(null)
const adxChartRef = ref(null)
const volumeChartRef = ref(null)
const macdChartRef = ref(null)
const rsiChartRef = ref(null)

const moneyflowLoading = ref(false)
const moneyflowData = ref([])
const showLargeOnly = ref(true)
const moneyflowChart = ref(null)
let moneyflowChartInstance = null

const chipLoading = ref(false)
const chipData = ref({ chips: [], current_price: null, trade_date: null })
const chipChartRef = ref(null)
const selectedChipDate = ref(null)

// 信号时间线数据
const signalsLoading = ref(false)
const signalList = ref([])

// AI 调研记录
const surveysLoading = ref(false)
const surveyList = ref([])

// 股票备注相关
const showNotesDialog = ref(false)
const stockNotesInput = ref('')
const notesLoading = ref(false)
const notesInputRef = ref(null)

// 所属分组相关
const watchlistStockInfo = ref(null)
const showSwitchGroupDialog = ref(false)
const selectedTargetWatchlist = ref(null)
const switchGroupReason = ref('')
const switchLoading = ref(false)
const availableWatchlists = ref([])

// 标签相关
const stockTags = ref([])
const allTags = ref([])
const tagPopoverVisible = ref(false)
const popoverSelectedTags = ref([])
const newTagInput = ref('')
const tagInputRef = ref(null)

// 股票信息相关
const stockInfos = ref([])
const showInfoDialog = ref(false)
const infoDialogMode = ref('create')
const editingInfoId = ref(null)
const infoMemoInput = ref('')
const infoLoading = ref(false)

// 关注弹窗相关
const followDialogVisible = ref(false)
const currentFollowStock = ref(null)
const isWatched = ref(false)

const conceptList = ref([])
const conceptLoading = ref(false)

const auditList = ref([])

const showSettingsDialog = ref(false)
const syncKlineLoading = ref(false)
const syncKlineResult = ref(null)
const deleteStockLoading = ref(false)

const router = useRouter()

// 板块类型计算属性
const boardType = computed(() => {
  if (!stock.value?.ts_code) return { emoji: '', label: '', type: 'info' }
  
  const code = stock.value.ts_code.split('.')[0]
  const prefix = code.substring(0, 3)
  const numCode = parseInt(code, 10)
  
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

// 复权方式: forward=前复权, backward=后复权, none=不复权
const adjType = ref('forward')

// 复权计算：对K线数据中的价格字段做前复权/后复权/不复权处理
// 前复权: price * adj_factor / latest_adj_factor (以最新价格为基准)
// 后复权: price * adj_factor / earliest_adj_factor (以最早价格为基准)
// 不复权: 原始价格
const applyAdjustment = (rawData) => {
  if (!rawData || rawData.length === 0 || adjType.value === 'none') return rawData

  const hasAdjFactor = rawData.some(item => item.adj_factor != null)
  if (!hasAdjFactor) return rawData

  const priceFields = ['open', 'high', 'low', 'close']

  if (adjType.value === 'forward') {
    // 前复权: 以最新日为基准
    // 找到最新的有效 adj_factor
    const latestAdj = [...rawData].reverse().find(item => item.adj_factor != null)?.adj_factor
    if (!latestAdj || latestAdj === 0) return rawData

    return rawData.map(item => {
      if (item.adj_factor == null) return item
      const ratio = item.adj_factor / latestAdj
      const adjusted = { ...item }
      priceFields.forEach(field => {
        if (adjusted[field] != null) {
          adjusted[field] = +(adjusted[field] * ratio).toFixed(2)
        }
      })
      return adjusted
    })
  }

  if (adjType.value === 'backward') {
    // 后复权: 以最早日为基准
    const earliestAdj = rawData.find(item => item.adj_factor != null)?.adj_factor
    if (!earliestAdj || earliestAdj === 0) return rawData

    return rawData.map(item => {
      if (item.adj_factor == null) return item
      const ratio = item.adj_factor / earliestAdj
      const adjusted = { ...item }
      priceFields.forEach(field => {
        if (adjusted[field] != null) {
          adjusted[field] = +(adjusted[field] * ratio).toFixed(2)
        }
      })
      return adjusted
    })
  }

  return rawData
}

// 调整后的日K线数据（用于所有日线图表组件）
const adjustedKlineData = computed(() => applyAdjustment(klineData.value))

// 调整后的周K线数据
const adjustedWeeklyKlineData = computed(() => applyAdjustment(weeklyKlineData.value))

// 可选标签列表（排除已选中的）
const availableTagsList = computed(() => {
  return allTags.value.filter(tag => !popoverSelectedTags.value.includes(tag))
})

// 筹码集中度 = (有筹码的最高价 - 有筹码的最低价) / (有筹码的最高价 + 有筹码的最低价)
const chipConcentration = computed(() => {
  const chips = chipData.value?.chips
  if (!chips || chips.length === 0) return null
  const prices = chips.filter(c => c.percent > 0).map(c => c.price)
  if (prices.length === 0) return null
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  if (maxPrice + minPrice === 0) return null
  return ((maxPrice - minPrice) / (maxPrice + minPrice)) * 100
})

// Ctrl+X 按键序列状态
let ctrlXPending = false
let ctrlXTimer = null

const handleKeydown = (e) => {
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault()
    if (showNotesDialog.value && stockNotesInput.value.trim() && !notesLoading.value) {
      saveStockNotes()
    }
  }
  // Ctrl+X 前缀
  if (e.ctrlKey && e.key === 'x') {
    e.preventDefault()
    ctrlXPending = true
    clearTimeout(ctrlXTimer)
    ctrlXTimer = setTimeout(() => { ctrlXPending = false }, 2000)
    return
  }
  if (ctrlXPending && e.key === 'o') {
    e.preventDefault()
    ctrlXPending = false
    clearTimeout(ctrlXTimer)
    if (stock.value) {
      openXueqiu(stock.value)
    }
  }
  // Ctrl+X -> N: 打开备注弹窗
  if (ctrlXPending && e.key === 'n') {
    e.preventDefault()
    ctrlXPending = false
    clearTimeout(ctrlXTimer)
    if (!showNotesDialog.value) {
      openNotesDialog()
    }
  }
  // Ctrl+X -> G: 打开标签编辑弹窗
  if (ctrlXPending && e.key === 'g') {
    e.preventDefault()
    ctrlXPending = false
    clearTimeout(ctrlXTimer)
    if (!tagPopoverVisible.value) {
      openTagPopover()
    }
  }
}

onMounted(() => {
  loadStockDetail()
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  if (moneyflowChartInstance) {
    moneyflowChartInstance.dispose()
    moneyflowChartInstance = null
  }

})

const handleResize = () => {
  klineChartRef.value?.resize()
  weeklyKlineChartRef.value?.resize()
  adxChartRef.value?.resize()
  volumeChartRef.value?.resize()
  macdChartRef.value?.resize()
  rsiChartRef.value?.resize()
  chipChartRef.value?.resize()
  if (moneyflowChartInstance) {
    moneyflowChartInstance.resize()
  }
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
    await loadSignal()
    await loadMoneyflow()
    await loadCyqChips()
    await loadSignals()
    await loadWatchlistStockInfo()
    await fetchWatchlistOptions()
    await loadTags()
    await loadAllTags()
    await loadStockInfos()
    await loadConcepts()
    await loadAudit()
    await loadSurveys()
  } catch (error) {
    console.error('Failed to load stock detail:', error)
    ElMessage.error('加载失败')
  }
}

const loadMoneyflow = async () => {
  moneyflowLoading.value = true
  try {
    const response = await basicDataApi.getMoneyflow(props.tsCode, 60)
    if (response.success) {
      moneyflowData.value = response.data || []
      if (moneyflowData.value.length > 0) {
        renderMoneyflowChart()
      }
    } else {
      ElMessage.error(response.error || '获取资金流向失败')
    }
  } catch (error) {
    console.error('Failed to load moneyflow:', error)
  } finally {
    moneyflowLoading.value = false
  }
}

const loadCyqChips = async (date = null) => {
  chipLoading.value = true
  try {
    const response = await basicDataApi.getCyqChips(props.tsCode, date)
    if (response.success && response.data) {
      chipData.value = {
        chips: response.data.chips || [],
        current_price: response.data.current_price || null,
        trade_date: response.data.trade_date || null
      }
    }
  } catch (error) {
    console.error('Failed to load cyq chips:', error)
  } finally {
    chipLoading.value = false
  }
}

// 日期选择变化时加载对应日期的筹码分布
const onChipDateChange = (date) => {
  if (date) {
    loadCyqChips(date)
  } else {
    loadCyqChips()
  }
}

const renderMoneyflowChart = () => {
  if (!moneyflowChart.value || moneyflowData.value.length === 0) return

  if (!moneyflowChartInstance) {
    moneyflowChartInstance = echarts.init(moneyflowChart.value)
  }

  const data = moneyflowData.value
  const dates = data.map(item => item.trade_date)

  const smNet = data.map(item => +(item.buy_sm_amount - item.sell_sm_amount).toFixed(2))
  const mdNet = data.map(item => +(item.buy_md_amount - item.sell_md_amount).toFixed(2))
  const lgNet = data.map(item => +(item.buy_lg_amount - item.sell_lg_amount).toFixed(2))
  const elgNet = data.map(item => +(item.buy_elg_amount - item.sell_elg_amount).toFixed(2))

  const colorPos = '#f56c6c'
  const colorNeg = '#67c23a'
  const toBarData = (arr) => arr.map(v => ({ value: v, itemStyle: { color: v >= 0 ? colorPos : colorNeg } }))

  const series = []

  if (!showLargeOnly.value) {
    series.push(
      { name: '小单(<5万)', type: 'bar', stack: 'moneyflow', data: toBarData(smNet) },
      { name: '中单(5万-20万)', type: 'bar', stack: 'moneyflow', data: toBarData(mdNet) }
    )
  }

  series.push(
    { name: '大单(20万-100万)', type: 'bar', stack: 'moneyflow', data: toBarData(lgNet) },
    { name: '特大单(>=100万)', type: 'bar', stack: 'moneyflow', data: toBarData(elgNet) }
  )

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: false,
      appendToBody: true,
      className: 'moneyflow-tooltip',
      formatter: (params) => {
        let html = `<div style="font-weight:bold;margin-bottom:5px">${params[0].name}</div>`
        let total = 0
        params.forEach(p => {
          const val = p.value
          total += val
          const color = val >= 0 ? '#f56c6c' : '#67c23a'
          html += `<div>${p.marker} ${p.seriesName}: <span style="color:${color};font-weight:bold">${val >= 0 ? '+' : ''}${val.toFixed(2)}万</span></div>`
        })
        const totalColor = total >= 0 ? '#f56c6c' : '#67c23a'
        html += `<div style="margin-top:5px;border-top:1px solid #eee;padding-top:5px;font-weight:bold">净流入: <span style="color:${totalColor}">${total >= 0 ? '+' : ''}${total.toFixed(2)}万</span></div>`
        return html
      }
    },
    legend: { show: false },
    grid: {
      left: '8%',
      right: '4%',
      bottom: '15%',
      top: '40px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value) => value.substring(5),
        fontSize: 9,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => {
          if (Math.abs(value) >= 10000) return (value / 10000).toFixed(1) + '亿'
          return value + '万'
        },
        fontSize: 9
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#eee' }
      }
    },
    dataZoom: [{ type: 'inside', start: 0, end: 100, zoomOnMouseWheel: false, moveOnMouseWheel: false }],
    series: series
  }

  moneyflowChartInstance.setOption(option, true)
}

// 资金流向汇总：5日/10日/20日净流入
const moneyflowSummary = computed(() => {
  const data = moneyflowData.value
  if (!data || data.length === 0) return null

  // 仅计算大单(20万-100万) + 特大单(>=100万)
  const calcNetInflow = (items) => {
    return items.reduce((sum, item) => {
      const net = (item.buy_lg_amount - item.sell_lg_amount)
        + (item.buy_elg_amount - item.sell_elg_amount)
      return sum + net
    }, 0)
  }

  // data 按 trade_date 排列，取末尾 N 条为最近 N 天
  const d5 = calcNetInflow(data.slice(-5))
  const d10 = calcNetInflow(data.slice(-10))
  const d20 = calcNetInflow(data.slice(-20))

  return { d5, d10, d20 }
})

const formatNetInflow = (val) => {
  if (val == null) return '-'
  const abs = Math.abs(val)
  let text
  if (abs >= 10000) text = (abs / 10000).toFixed(2) + '亿'
  else text = abs.toFixed(2) + '万'
  return (val >= 0 ? '+' : '') + text
}

watch(showLargeOnly, () => {
  if (moneyflowData.value.length > 0) {
    renderMoneyflowChart()
  }
})

const loadKline = async () => {
  try {
    const dailyResponse = await stockApi.getKline(props.tsCode, 'daily', 120)
    klineData.value = dailyResponse.data.data || []
  } catch (error) {
    console.error('Failed to load daily kline:', error)
  }
  try {
    const weeklyResponse = await stockApi.getKline(props.tsCode, 'weekly', 60)
    weeklyKlineData.value = weeklyResponse.data.data || []
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

const loadSignal = async () => {
  try {
    const response = await signalApi.getLatest(props.tsCode)
    latestSignal.value = response.data
  } catch (error) {
    console.error('Failed to load signal:', error)
  }
}

const loadSignals = async () => {
  signalsLoading.value = true
  try {
    const response = await signalApi.getAll({
      ts_code: props.tsCode,
      active_only: false,
      limit: 100
    })
    if (response.success) {
      signalList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load signals:', error)
  } finally {
    signalsLoading.value = false
  }
}

const loadSurveys = async () => {
  surveysLoading.value = true
  try {
    const response = await aiChatApi.getSurveys(props.tsCode)
    if (response.success) {
      surveyList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load surveys:', error)
  } finally {
    surveysLoading.value = false
  }
}

const renderSurveyContent = (content) => {
  if (!content) return ''
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

const getChangeClass = (change) => {
  if (!change) return ''
  return change > 0 ? 'up' : change < 0 ? 'down' : ''
}

const getSignalType = (type) => {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'info', NOTE: 'warning', ADD_TAG: '' }
  return map[type] || 'info'
}

const getSignalTimelineType = (type) => {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'primary', NOTE: 'warning', ADD_TAG: 'primary' }
  return map[type] || 'primary'
}

const formatSignal = (type) => {
  const map = { BUY: '买入', SELL: '卖出', WATCH: '观望', NOTE: '备注', ADD_TAG: '添加标签' }
  return map[type] || type
}

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

const formatMarketCap = (cap) => {
  if (!cap) return '-'
  // total_mv from tushare daily_basic is in 万元, 10000万 = 1亿
  return (cap / 10000).toFixed(2) + '亿'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-')
}

// 打开雪球网
const openXueqiu = (stock) => {
  if (!stock || !stock.ts_code) return
  // 转换格式: 300006.SZ -> SZ300006
  const [code, exchange] = stock.ts_code.split('.')
  const xueqiuCode = exchange + code
  window.open(`https://xueqiu.com/S/${xueqiuCode}`, '_blank')
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

// 获取所有分组选项
const fetchWatchlistOptions = async () => {
  try {
    const response = await watchlistApi.getAll()
    if (response.success) {
      availableWatchlists.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to fetch watchlists:', error)
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

// 加载所有可用标签
const loadAllTags = async () => {
  try {
    const response = await watchlistApi.getAllTags()
    if (response.success) {
      allTags.value = response.data?.tags || []
    }
  } catch (error) {
    console.error('Failed to load all tags:', error)
  }
}

// 打开标签编辑弹窗
const openTagPopover = () => {
  popoverSelectedTags.value = [...stockTags.value]
  newTagInput.value = ''
  tagPopoverVisible.value = true
}

// 添加新标签（通过输入框）
const addNewTag = () => {
  const tag = newTagInput.value.trim()
  if (tag && !popoverSelectedTags.value.includes(tag)) {
    popoverSelectedTags.value.push(tag)
  }
  newTagInput.value = ''
}

// 添加已有标签（点击可选标签）
const addSelectedTag = (tag) => {
  if (!popoverSelectedTags.value.includes(tag)) {
    popoverSelectedTags.value.push(tag)
  }
}

// 移除已选标签
const removeSelectedTag = (tag) => {
  const index = popoverSelectedTags.value.indexOf(tag)
  if (index > -1) {
    popoverSelectedTags.value.splice(index, 1)
  }
}

// 保存股票标签
const saveStockTags = async () => {
  try {
    // 计算新增的标签
    const newTags = popoverSelectedTags.value.filter(tag => !stockTags.value.includes(tag))

    const response = await stockApi.updateTags(props.tsCode, popoverSelectedTags.value)
    if (response.success) {
      stockTags.value = [...popoverSelectedTags.value]
      tagPopoverVisible.value = false
      ElMessage.success('标签更新成功')
      await loadAllTags()

      // 如果有新增标签，发送 ADD_TAG 信号
      if (newTags.length > 0) {
        const signalResponse = await signalApi.addTag(props.tsCode, newTags)
        if (signalResponse.success) {
          signalList.value.unshift({
            id: signalResponse.data?.id || Date.now(),
            ts_code: props.tsCode,
            signal_type: 'ADD_TAG',
            note_content: newTags.join(', '),
            created_at: new Date().toISOString(),
            signal_date: new Date().toISOString()
          })
        }
      }
    } else {
      ElMessage.error(response.error || '标签更新失败')
    }
  } catch (error) {
    console.error('Failed to save tags:', error)
    ElMessage.error('标签更新失败')
  }
}

// 打开切换分组弹窗
const openSwitchGroupDialog = () => {
  selectedTargetWatchlist.value = null
  switchGroupReason.value = ''
  showSwitchGroupDialog.value = true
}

// 切换股票分组
const switchStockGroup = async () => {
  if (!watchlistStockInfo.value || !selectedTargetWatchlist.value) return
  if (!switchGroupReason.value.trim()) {
    ElMessage.warning('请填写变更理由')
    return
  }

  switchLoading.value = true
  try {
    await watchlistApi.moveStockToWatchlist(
      watchlistStockInfo.value.id,
      selectedTargetWatchlist.value,
      switchGroupReason.value.trim()
    )
    ElMessage.success('切换分组成功')
    showSwitchGroupDialog.value = false
    await loadWatchlistStockInfo()
  } catch (error) {
    console.error('Failed to switch stock group:', error)
    ElMessage.error('切换分组失败')
  } finally {
    switchLoading.value = false
  }
}

// 打开股票备注弹窗
const openNotesDialog = () => {
  stockNotesInput.value = ''
  showNotesDialog.value = true
}

// 弹窗打开动画结束后聚焦输入框
const onNotesDialogOpened = () => {
  notesInputRef.value?.focus()
}

const saveStockNotes = async () => {
  if (!stock.value || !stock.value.ts_code) return

  notesLoading.value = true
  const notesContent = stockNotesInput.value.trim()
  try {
    const response = await signalApi.addNote(stock.value.ts_code, notesContent)
    if (response.success) {
      showNotesDialog.value = false

      signalList.value.unshift({
        id: response.data?.id || Date.now(),
        ts_code: stock.value.ts_code,
        signal_type: 'NOTE',
        note_content: notesContent,
        created_at: new Date().toISOString(),
        signal_date: new Date().toISOString()
      })

      if (watchlistStockInfo.value) {
        watchlistStockInfo.value.notes = notesContent
      }

      ElMessage.success('备注添加成功')
    } else {
      ElMessage.error(response.error || '备注更新失败')
    }
  } catch (error) {
    console.error('Failed to update stock notes:', error)
    ElMessage.error('备注更新失败')
  } finally {
    notesLoading.value = false
  }
}

// 加载股票信息
const loadStockInfos = async () => {
  try {
    const response = await stockInfoApi.get(props.tsCode)
    if (response.success) {
      stockInfos.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load stock infos:', error)
  }
}

// 打开添加信息弹窗
const openCreateInfoDialog = () => {
  infoDialogMode.value = 'create'
  editingInfoId.value = null
  infoMemoInput.value = ''
  showInfoDialog.value = true
}

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

const loadAudit = async () => {
  try {
    const response = await basicDataApi.getFinaAudit(props.tsCode, 5)
    if (response.success) {
      auditList.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load audit:', error)
  }
}

const formatEndDate = (dateStr) => {
  if (!dateStr) return '-'
  // end_date like "2024-12-31" -> "2024年报"
  const parts = dateStr.split('-')
  const year = parts[0]
  const month = parseInt(parts[1], 10)
  if (month === 12) return `${year}年报`
  if (month === 9) return `${year}三季报`
  if (month === 6) return `${year}中报`
  if (month === 3) return `${year}一季报`
  return dateStr
}

const getAuditTagType = (result) => {
  if (!result) return 'info'
  if (result.includes('标准无保留意见') || result.includes('无保留意见')) return 'success'
  if (result.includes('保留意见')) return 'warning'
  if (result.includes('否定意见') || result.includes('无法表示意见')) return 'danger'
  return 'info'
}

const handleSyncKline = async () => {
  syncKlineLoading.value = true
  syncKlineResult.value = null
  try {
    const response = await stockApi.syncKline(props.tsCode)
    syncKlineResult.value = response
    if (response.success) {
      ElMessage.success('K线数据同步完成')
      await loadKline()
    } else {
      ElMessage.error(response.error || '同步失败')
    }
  } catch (error) {
    console.error('Failed to sync kline:', error)
    syncKlineResult.value = { success: false, error: error.message || '请求失败' }
    ElMessage.error('同步请求失败')
  } finally {
    syncKlineLoading.value = false
  }
}

const handleDeleteStock = async () => {
  if (!watchlistStockInfo.value) return
  deleteStockLoading.value = true
  try {
    await watchlistApi.removeStock(
      watchlistStockInfo.value.watchlist_id,
      watchlistStockInfo.value.id
    )
    ElMessage.success('删除成功')
    showSettingsDialog.value = false
    router.push({ path: '/watchlist' })
  } catch (error) {
    console.error('Failed to delete stock:', error)
    ElMessage.error('删除失败')
  } finally {
    deleteStockLoading.value = false
  }
}

// 打开编辑信息弹窗
const openEditInfoDialog = (info) => {
  infoDialogMode.value = 'edit'
  editingInfoId.value = info.id
  infoMemoInput.value = info.memo || ''
  showInfoDialog.value = true
}

// 保存股票信息
const saveStockInfo = async () => {
  if (!stock.value || !stock.value.ts_code) return

  infoLoading.value = true
  const memoContent = infoMemoInput.value.trim()

  try {
    let response
    if (infoDialogMode.value === 'create') {
      response = await stockInfoApi.create({ ts_code: stock.value.ts_code, memo: memoContent })
    } else {
      response = await stockInfoApi.update(editingInfoId.value, { memo: memoContent })
    }

    if (response.success) {
      showInfoDialog.value = false
      ElMessage.success(infoDialogMode.value === 'create' ? '信息添加成功' : '信息更新成功')
      await loadStockInfos()
    } else {
      ElMessage.error(response.error || '保存失败')
    }
  } catch (error) {
    console.error('Failed to save stock info:', error)
    ElMessage.error('保存失败')
  } finally {
    infoLoading.value = false
  }
}

// 删除股票信息
const deleteStockInfo = async (infoId) => {
  try {
    const response = await stockInfoApi.delete(infoId)
    if (response.success) {
      ElMessage.success('删除成功')
      await loadStockInfos()
    } else {
      ElMessage.error(response.error || '删除失败')
    }
  } catch (error) {
    console.error('Failed to delete stock info:', error)
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.stock-detail {
  padding: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.weekly-kline-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.adj-type-selector :deep(.el-radio-button__inner) {
  padding: 4px 10px;
  font-size: 12px;
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
  color: #303133;
}

.stock-info-top__change {
  font-size: 16px;
  font-weight: 600;
}

.stock-info-top__change.up {
  color: #f56c6c;
}

.stock-info-top__change.down {
  color: #67c23a;
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

.stock-info-top__metric .metric-label {
  font-size: 12px;
  color: #909399;
}

.stock-info-top__metric .metric-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
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

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
}

.info-item .label {
  color: #606266;
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
  color: #606266;
}

.signal-details {
  padding: 10px 0;
}

.signal-item {
  margin-bottom: 15px;
}

.signal-item .label {
  display: block;
  color: #606266;
  margin-bottom: 5px;
}

.indicators {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.moneyflow-summary {
  display: flex;
  justify-content: space-around;
  padding: 10px 0 6px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.moneyflow-summary .summary-item {
  text-align: center;
}

.moneyflow-summary .summary-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.moneyflow-summary .summary-value {
  font-size: 15px;
  font-weight: 600;
}

.moneyflow-summary .summary-value.up {
  color: #f56c6c;
}

.moneyflow-summary .summary-value.down {
  color: #67c23a;
}

.moneyflow-legend {
  display: flex;
  align-items: center;
  gap: 12px;
}

.moneyflow-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.moneyflow-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.moneyflow-legend .dot.red {
  background-color: #f56c6c;
}

.moneyflow-legend .dot.green {
  background-color: #67c23a;
}

/* 信号时间线样式 */
.signal-timeline-card {
  height: 480px;
  overflow-y: auto;
}

.stock-survey-card {
  max-height: 1000px;
  overflow-y: auto;
}

.survey-timeline-content {
  padding: 8px 0;
}

.survey-query {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  padding: 8px 10px;
  background-color: #f4f4f5;
  border-radius: 4px;
}

.survey-result {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  word-break: break-word;
}

.survey-result pre {
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
}

.survey-result code {
  background: #f5f7fa;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}

.signal-count {
  font-size: 12px;
  color: #909399;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.empty-signals {
  padding: 20px 0;
}

.signal-timeline-content {
  padding: 8px 0;
}

.signal-timeline-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.signal-date {
  font-size: 12px;
  color: #909399;
}

.signal-strength {
  font-size: 12px;
  color: #606266;
}

.signal-note {
  padding: 10px 12px;
  background-color: #fdf6ec;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.signal-tags {
  padding: 10px 12px;
  background-color: #f4f4f5;
  border-radius: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.signal-result {
  padding: 10px 12px;
  background-color: #f4f4f5;
  border-radius: 4px;
}

.result-text {
  color: #303133;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-empty {
  color: #909399;
  font-size: 13px;
  font-style: italic;
}

.signal-indicators-mini {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}

/* 资金流向 tooltip 层级 */
:global(.moneyflow-tooltip) {
  z-index: 9999 !important;
}

/* ADX 图例 */
.adx-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #606266;
}

/* 成交量图例 */
.volume-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #606266;
}

.volume-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.volume-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.kline-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.signal-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #606266;
}

.signal-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.signal-legend .legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.signal-legend .legend-tri {
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-bottom: 8px solid #409eff;
}

.signal-legend .legend-diamond {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #9c27b0;
  transform: rotate(45deg);
}

.signal-legend .legend-rect {
  display: inline-block;
  width: 10px;
  height: 10px;
  background: #fff;
  border: 2px solid #e6a23c;
  box-shadow: inset 0 0 0 1.5px #409eff;
}

/* MACD 图例 */
.macd-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #606266;
}

.macd-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.macd-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.adx-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.adx-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* 指标说明卡片 */
.indicator-guide-card .guide-feature {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 8px 10px;
  background-color: #f0f9eb;
  border-radius: 4px;
}

.indicator-guide-card .guide-section {
  margin-bottom: 10px;
}

.indicator-guide-card .guide-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}

.indicator-guide-card .guide-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}

.indicator-guide-card .guide-summary {
  font-size: 13px;
  color: #303133;
  line-height: 1.8;
}

.indicator-guide-card .summary-line {
  margin-bottom: 4px;
}

.indicator-guide-card .summary-label {
  font-weight: 600;
  color: #303133;
}

/* 筹码分布 */
.chip-date {
  font-size: 12px;
  color: #909399;
}

.chip-summary {
  display: flex;
  justify-content: space-around;
  padding: 10px 0 6px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.chip-summary .summary-item {
  text-align: center;
}

.chip-summary .summary-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.chip-summary .summary-value {
  font-size: 15px;
  font-weight: 600;
  color: #409eff;
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
  color: #909399;
}

/* 已选标签容器 */
.selected-tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  min-height: 32px;
  width: 100%;
}

.selected-tag {
  margin: 0;
}

.tag-input {
  width: 120px;
  flex-shrink: 1;
}

.tag-input :deep(.el-input__wrapper) {
  box-shadow: none;
}

/* 可选标签容器 */
.available-tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.available-tag {
  margin: 0;
  cursor: pointer;
  transition: all 0.2s;
}

.available-tag:hover {
  color: #409eff;
  border-color: #409eff;
  background-color: #ecf5ff;
}

/* 股票信息列表 */
.stock-infos-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stock-info-item {
  position: relative;
  padding: 10px 12px;
  background-color: #f4f4f5;
  border-radius: 4px;
  transition: all 0.2s;
}

.stock-info-item:hover {
  background-color: #e9e9eb;
}

.stock-info-item:hover .info-actions {
  opacity: 1;
}

.info-content {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.info-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
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

.sync-kline-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sync-kline-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

.sync-result {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 4px;
  line-height: 1.5;
}

.sync-result.sync-success {
  background-color: #f0f9eb;
  color: #67c23a;
}

.sync-result.sync-error {
  background-color: #fef0f0;
  color: #f56c6c;
}

.delete-stock-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.delete-stock-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

/* 审计意见 */
.audit-card {
  margin-bottom: 20px;
}

.audit-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.audit-item {
  padding: 8px 10px;
  background-color: #f4f4f5;
  border-radius: 4px;
}

.audit-item__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.audit-item__period {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.audit-item__agency {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
