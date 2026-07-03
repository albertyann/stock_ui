/**
 * K-line 数据处理工具函数
 */

const PRICE_FIELDS = ['open', 'high', 'low', 'close']

/**
 * 前复权处理：以最新交易日为基准，对 K 线数据中的价格字段做前复权
 *
 * 前复权公式: adjusted_price = price * adj_factor / latest_adj_factor
 *
 * @param {Array} rawData - 原始 K 线数据，每项需包含 adj_factor 及价格字段
 * @returns {Array} 前复权后的数据，若无复权因子则返回原始数据
 */
export function forwardAdjustKlineData(rawData) {
  if (!rawData || rawData.length === 0) return rawData

  const hasAdjFactor = rawData.some(item => item.adj_factor != null)
  if (!hasAdjFactor) return rawData

  // 找到最新的有效 adj_factor（以最新日期为基准）
  const latestAdj = [...rawData].reverse().find(item => item.adj_factor != null)?.adj_factor
  if (!latestAdj || latestAdj === 0) return rawData

  return rawData.map(item => {
    if (item.adj_factor == null) return item
    const ratio = item.adj_factor / latestAdj
    const adjusted = { ...item }
    PRICE_FIELDS.forEach(field => {
      if (adjusted[field] != null) {
        adjusted[field] = +(adjusted[field] * ratio).toFixed(2)
      }
    })
    return adjusted
  })
}
