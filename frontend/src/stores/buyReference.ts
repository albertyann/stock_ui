import { defineStore } from 'pinia'
import type { BuySignal, SignalFilter, SignalSorter } from '@/types/buy-reference'
import { StrategyType, SignalStatus } from '@/types/buy-reference'

// 模拟策略数据
const MOCK_SIGNALS: BuySignal[] = [
  {
    id: '1',
    stock: {
      tsCode: '000001.SZ',
      symbol: '000001',
      name: '平安银行'
    },
    strategy: {
      id: 'breakout-ma20',
      name: '突破20日均线策略',
      type: StrategyType.BREAKOUT
    },
    strength: 85,
    reasons: [
      {
        type: 'trend',
        title: '趋势突破',
        description: '股价突破20日均线，且成交量放大',
        indicator: 'MA20',
        value: 10.92,
        weight: 0.4,
        satisfied: true
      },
      {
        type: 'volume',
        title: '量能配合',
        description: '成交量较5日均量放大150%',
        indicator: 'Volume Ratio',
        value: '1.5x',
        weight: 0.3,
        satisfied: true
      },
      {
        type: 'momentum',
        title: '动量向上',
        description: 'MACD金叉，动能增强',
        indicator: 'MACD',
        value: 0.25,
        weight: 0.3,
        satisfied: true
      }
    ],
    indicators: {
      ma5: 10.85,
      ma10: 10.78,
      ma20: 10.68,
      rsi: 58,
      macd: 0.25
    },
    priceRange: {
      low: 10.80,
      high: 11.00,
      current: 10.92
    },
    stopLoss: 10.50,
    createdAt: new Date('2026-03-16'),
    status: SignalStatus.ACTIVE
  },
  {
    id: '2',
    stock: {
      tsCode: '002415.SZ',
      symbol: '002415',
      name: '海康威视'
    },
    strategy: {
      id: 'momentum-rsi',
      name: '动量反转策略',
      type: StrategyType.MOMENTUM
    },
    strength: 72,
    reasons: [
      {
        type: 'momentum',
        title: 'RSI超卖反弹',
        description: 'RSI从超卖区(30以下)反弹，动能转强',
        indicator: 'RSI',
        value: 35,
        weight: 0.5,
        satisfied: true
      },
      {
        type: 'support_resistance',
        title: '支撑有效',
        description: '在30元支撑位获得支撑，未跌破',
        indicator: 'Support',
        value: 30.00,
        weight: 0.5,
        satisfied: true
      }
    ],
    indicators: {
      ma5: 31.20,
      ma10: 31.50,
      ma20: 32.10,
      rsi: 35,
      macd: -0.15
    },
    priceRange: {
      low: 31.00,
      high: 32.50,
      current: 31.94
    },
    stopLoss: 29.80,
    createdAt: new Date('2026-03-15'),
    status: SignalStatus.ACTIVE
  },
  {
    id: '3',
    stock: {
      tsCode: '600519.SH',
      symbol: '600519',
      name: '贵州茅台'
    },
    strategy: {
      id: 'multi-factor',
      name: '多因子综合策略',
      type: StrategyType.MULTI_FACTOR
    },
    strength: 90,
    reasons: [
      {
        type: 'fundamental',
        title: '基本面优秀',
        description: 'ROE > 20%，毛利率 > 90%',
        indicator: 'ROE',
        value: '25%',
        weight: 0.3,
        satisfied: true
      },
      {
        type: 'trend',
        title: '长期趋势向上',
        description: '股价站稳60日均线，长期趋势良好',
        indicator: 'MA60',
        value: 1580,
        weight: 0.4,
        satisfied: true
      },
      {
        type: 'pattern',
        title: '杯柄形态',
        description: '形成经典杯柄形态，突破颈线',
        indicator: 'Pattern',
        value: 'Cup & Handle',
        weight: 0.3,
        satisfied: true
      }
    ],
    indicators: {
      ma5: 1590,
      ma10: 1585,
      ma20: 1580,
      ma60: 1560,
      rsi: 55,
      macd: 2.5
    },
    priceRange: {
      low: 1580,
      high: 1620,
      current: 1588
    },
    stopLoss: 1550,
    createdAt: new Date('2026-03-14'),
    status: SignalStatus.ACTIVE
  },
  {
    id: '4',
    stock: {
      tsCode: '002594.SZ',
      symbol: '002594',
      name: '比亚迪'
    },
    strategy: {
      id: 'technical-breakout',
      name: '技术形态突破策略',
      type: StrategyType.TECHNICAL
    },
    strength: 78,
    reasons: [
      {
        type: 'pattern',
        title: '三角形整理突破',
        description: '收敛三角形整理后向上突破',
        indicator: 'Pattern',
        value: 'Triangle Breakout',
        weight: 0.6,
        satisfied: true
      },
      {
        type: 'volume',
        title: '放量突破',
        description: '突破时成交量放大2倍',
        indicator: 'Volume',
        value: '2.1x',
        weight: 0.4,
        satisfied: true
      }
    ],
    indicators: {
      ma5: 268,
      ma10: 265,
      ma20: 260,
      rsi: 62,
      macd: 1.8
    },
    priceRange: {
      low: 265,
      high: 275,
      current: 268.5
    },
    stopLoss: 258,
    createdAt: new Date('2026-03-16'),
    status: SignalStatus.ACTIVE
  }
]

export const useBuyReferenceStore = defineStore('buyReference', {
  state: () => ({
    signals: [] as BuySignal[],
    loading: false,
    selectedSignals: [] as string[],
    filter: {
      strategyTypes: [] as StrategyType[],
      minStrength: 0,
      maxStrength: 100,
      status: [SignalStatus.ACTIVE]
    } as SignalFilter,
    sorter: {
      field: 'strength',
      direction: 'desc'
    } as SignalSorter,
    lastUpdated: null as Date | null,
    error: null as string | null
  }),

  getters: {
    // 过滤后的信号
    filteredSignals: (state) => {
      let result = [...state.signals]

      // 应用过滤器
      if (state.filter.strategyTypes?.length) {
        result = result.filter(s => 
          state.filter.strategyTypes?.includes(s.strategy.type)
        )
      }

      if (state.filter.minStrength !== undefined) {
        result = result.filter(s => s.strength >= (state.filter.minStrength || 0))
      }

      if (state.filter.maxStrength !== undefined) {
        result = result.filter(s => s.strength <= (state.filter.maxStrength || 100))
      }

      if (state.filter.status?.length) {
        result = result.filter(s => 
          state.filter.status?.includes(s.status)
        )
      }

      // 应用排序
      result.sort((a, b) => {
        const field = state.sorter.field
        const direction = state.sorter.direction === 'asc' ? 1 : -1

        if (field === 'strength') {
          return (a.strength - b.strength) * direction
        }
        if (field === 'createdAt') {
          return (new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()) * direction
        }
        if (field === 'strategy') {
          return a.strategy.name.localeCompare(b.strategy.name) * direction
        }
        if (field === 'stock') {
          return a.stock.name.localeCompare(b.stock.name) * direction
        }
        return 0
      })

      return result
    },

    // 按策略分组
    signalsByStrategy: (state) => {
      const grouped = new Map()
      state.signals.forEach(signal => {
        const key = signal.strategy.id
        if (!grouped.has(key)) {
          grouped.set(key, {
            strategy: signal.strategy,
            signals: []
          })
        }
        grouped.get(key).signals.push(signal)
      })
      return Array.from(grouped.values())
    },

    // 统计信息
    stats: (state) => {
      return {
        total: state.signals.length,
        active: state.signals.filter(s => s.status === SignalStatus.ACTIVE).length,
        watching: state.signals.filter(s => s.status === SignalStatus.WATCHING).length,
        executed: state.signals.filter(s => s.status === SignalStatus.EXECUTED).length,
        avgStrength: state.signals.length > 0
          ? state.signals.reduce((sum, s) => sum + s.strength, 0) / state.signals.length
          : 0
      }
    }
  },

  actions: {
    // 加载信号列表
    async fetchSignals() {
      this.loading = true
      this.error = null
      
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 500))
        this.signals = MOCK_SIGNALS
        this.lastUpdated = new Date()
      } catch (err) {
        this.error = '加载失败'
        console.error('Failed to fetch signals:', err)
      } finally {
        this.loading = false
      }
    },

    // 刷新信号
    async refresh() {
      await this.fetchSignals()
    },

    // 更新过滤器
    updateFilter(filter: Partial<SignalFilter>) {
      this.filter = { ...this.filter, ...filter }
    },

    // 更新排序
    updateSorter(sorter: SignalSorter) {
      this.sorter = sorter
    },

    // 选择/取消选择信号
    toggleSelection(signalId: string) {
      const index = this.selectedSignals.indexOf(signalId)
      if (index > -1) {
        this.selectedSignals.splice(index, 1)
      } else {
        this.selectedSignals.push(signalId)
      }
    },

    // 全选
    selectAll() {
      this.selectedSignals = this.filteredSignals.map(s => s.id)
    },

    // 取消全选
    deselectAll() {
      this.selectedSignals = []
    },

    // 移除信号
    async removeSignal(signalId: string) {
      const index = this.signals.findIndex(s => s.id === signalId)
      if (index > -1) {
        this.signals.splice(index, 1)
        // 从选中列表中移除
        const selectedIndex = this.selectedSignals.indexOf(signalId)
        if (selectedIndex > -1) {
          this.selectedSignals.splice(selectedIndex, 1)
        }
      }
    },

    // 批量移除
    async removeSignals(signalIds: string[]) {
      this.signals = this.signals.filter(s => !signalIds.includes(s.id))
      this.selectedSignals = this.selectedSignals.filter(id => !signalIds.includes(id))
    },

    // 添加到观察池
    async addToWatchlist(signalId: string, watchlistId: string) {
      const signal = this.signals.find(s => s.id === signalId)
      if (signal) {
        signal.status = SignalStatus.WATCHING
        // 这里可以调用API添加到观察池
        console.log(`Added ${signal.stock.name} to watchlist ${watchlistId}`)
      }
    },

    // 标记为已执行
    async markAsExecuted(signalId: string) {
      const signal = this.signals.find(s => s.id === signalId)
      if (signal) {
        signal.status = SignalStatus.EXECUTED
      }
    },

    // 获取信号详情
    getSignalById(signalId: string): BuySignal | undefined {
      return this.signals.find(s => s.id === signalId)
    }
  }
})
