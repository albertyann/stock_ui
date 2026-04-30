import { defineStore } from 'pinia'
import type { BuySignal, SignalFilter, SignalSorter } from '@/types/buy-reference'
import { StrategyType, SignalStatus } from '@/types/buy-reference'
import { signalApi } from '@/api'

export const useBuyReferenceStore = defineStore('buyReference', {
  state: () => ({
    signals: [] as BuySignal[],
    loading: false,
    selectedSignals: [] as string[],
    selectedDate: null as string | null,
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
    _mapApiSignalToBuySignal(apiSignal: any): BuySignal {
      const tsCode = apiSignal.ts_code || ''
      const symbol = tsCode.split('.')[0] || tsCode

      let strategyType = StrategyType.TECHNICAL
      const signalType = (apiSignal.signal_type || '').toLowerCase()
      const strategyName = apiSignal.strategy_name || apiSignal.signal_type || '未知策略'
      
      switch (signalType) {
        case 'breakout':
        case 'buy':
          strategyType = StrategyType.BREAKOUT
          break
        case 'momentum':
          strategyType = StrategyType.MOMENTUM
          break
        case 'reversal':
          strategyType = StrategyType.REVERSAL
          break
        case 'mean_reversion':
          strategyType = StrategyType.MEAN_REVERSION
          break
        case 'multi_factor':
          strategyType = StrategyType.MULTI_FACTOR
          break
        case 'technical':
          strategyType = StrategyType.TECHNICAL
          break
        case 'fundamental':
          strategyType = StrategyType.FUNDAMENTAL
          break
      }

      const reasons = []
      if (apiSignal.conditions_met && Array.isArray(apiSignal.conditions_met)) {
        apiSignal.conditions_met.forEach((condition: any, index: number) => {
          if (typeof condition === 'string') {
            reasons.push({
              type: 'indicator' as any,
              title: condition,
              description: condition,
              weight: 1 / apiSignal.conditions_met.length,
              satisfied: true
            })
          } else if (typeof condition === 'object') {
            reasons.push({
              type: (condition.type || 'indicator') as any,
              title: condition.title || condition.name || condition.indicator || `条件${index + 1}`,
              description: condition.description || condition.detail || condition.title || '',
              indicator: condition.indicator,
              value: condition.value,
              weight: condition.weight || (1 / apiSignal.conditions_met.length),
              satisfied: condition.satisfied !== false
            })
          }
        })
      }

      if (reasons.length === 0) {
        reasons.push({
          type: 'indicator' as any,
          title: strategyName,
          description: `${strategyName} 发出买入信号`,
          weight: 1,
          satisfied: true
        })
      }

      const currentPrice = apiSignal.current_price
      const targetPrice = apiSignal.target_price
      let priceRange = undefined
      if (currentPrice !== null && currentPrice !== undefined) {
        priceRange = {
          low: Math.min(currentPrice, targetPrice ?? currentPrice),
          high: Math.max(currentPrice, targetPrice ?? currentPrice),
          current: currentPrice
        }
      }

      let status = SignalStatus.ACTIVE
      if (apiSignal.is_active === false) {
        status = SignalStatus.EXPIRED
      }

      return {
        id: String(apiSignal.id || apiSignal.signal_id || ''),
        stock: {
          tsCode: tsCode,
          symbol: symbol,
          name: apiSignal.stock_name || symbol || tsCode,
          industry: apiSignal.industry || undefined,
          changePct: apiSignal.change_pct !== null && apiSignal.change_pct !== undefined ? Number(apiSignal.change_pct) : undefined
        },
        strategy: {
          id: signalType || 'unknown',
          name: strategyName,
          type: strategyType
        },
        strength: apiSignal.signal_strength || 0,
        reasons: reasons,
        indicators: apiSignal.indicators || undefined,
        priceRange: priceRange,
        stopLoss: apiSignal.stop_loss_price || undefined,
        createdAt: new Date(apiSignal.signal_date || apiSignal.created_at || new Date()),
        status: status
      }
    },

    async fetchSignals(date?: string) {
      this.loading = true
      this.error = null
      
      try {
        const params: any = { page: 1, page_size: 100 }
        if (date) {
          params.signal_date = date
        }
        const res = await signalApi.getSignalsManage(params)
        if (res.success) {
          this.signals = (res.data || [])
            .filter((s: any) => {
              const signalType = (s.signal_type || '').toLowerCase()
              return signalType !== 'note' && signalType !== 'add_tag'
            })
            .map((s: any) => this._mapApiSignalToBuySignal(s))
        } else {
          this.error = res.error || '加载失败'
          this.signals = []
        }
        this.lastUpdated = new Date()
      } catch (err) {
        this.error = '加载失败'
        this.signals = []
        console.error('Failed to fetch signals:', err)
      } finally {
        this.loading = false
      }
    },

    async refresh() {
      await this.fetchSignals(this.selectedDate || undefined)
    },

    updateFilter(filter: Partial<SignalFilter>) {
      this.filter = { ...this.filter, ...filter }
    },

    updateSorter(sorter: SignalSorter) {
      this.sorter = sorter
    },

    toggleSelection(signalId: string) {
      const index = this.selectedSignals.indexOf(signalId)
      if (index > -1) {
        this.selectedSignals.splice(index, 1)
      } else {
        this.selectedSignals.push(signalId)
      }
    },

    selectAll() {
      this.selectedSignals = this.filteredSignals.map(s => s.id)
    },

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
