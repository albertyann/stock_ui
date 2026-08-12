import { ref, computed } from 'vue'

// 日K主图请求与显示的交易日数：请求更多用于指标计算，视口只显示最近 N 天
export const KLINE_DISPLAY_DAYS = 90
export const INDICATOR_DISPLAY_DAYS = 120
export const KLINE_LOAD_DAYS = 180

/**
 * K线复权方式与复权后数据。
 *
 * @param {import('vue').Ref<Array>} klineData - 原始日K数据（时间升序）
 * @param {import('vue').Ref<Array>} weeklyKlineData - 原始周K数据（时间升序）
 *
 * @returns {{
 *   adjType: import('vue').Ref<'forward' | 'backward' | 'none'>,
 *   adjustedKlineData: import('vue').ComputedRef<Array>,
 *   indicatorKlineData: import('vue').ComputedRef<Array>,
 *   adjustedWeeklyKlineData: import('vue').ComputedRef<Array>,
 *   applyAdjustment: (rawData: Array) => Array
 * }}
 */
export function useKlineAdjust(klineData, weeklyKlineData) {
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

  // 下方指标卡片统一显示最近 120 天
  const indicatorKlineData = computed(() => {
    const data = adjustedKlineData.value
    if (!data || data.length <= INDICATOR_DISPLAY_DAYS) return data
    return data.slice(-INDICATOR_DISPLAY_DAYS)
  })

  // 调整后的周K线数据
  const adjustedWeeklyKlineData = computed(() => applyAdjustment(weeklyKlineData.value))

  return {
    adjType,
    adjustedKlineData,
    indicatorKlineData,
    adjustedWeeklyKlineData,
    applyAdjustment
  }
}
