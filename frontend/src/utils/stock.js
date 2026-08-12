/**
 * 股票/板块通用的格式化与分类工具
 */

/**
 * 根据涨跌幅返回 CSS 类名
 * @param {number} changePct
 * @returns {'up' | 'down' | 'flat'}
 */
export function getChangeClass(changePct) {
  if (changePct > 0) return 'up'
  if (changePct < 0) return 'down'
  return 'flat'
}

/**
 * 格式化涨跌幅为可读字符串
 * @param {number} changePct
 * @returns {string}
 */
export function formatChange(changePct) {
  if (changePct === null || changePct === undefined) return '-'
  if (changePct > 0) return `+${changePct.toFixed(2)}%`
  if (changePct < 0) return `${changePct.toFixed(2)}%`
  return '0.00%'
}

/**
 * 格式化成交量
 * @param {number} volume
 * @returns {string}
 */
export function formatVolume(volume) {
  if (!volume) return '-'
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  }
  if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  }
  return volume.toString()
}

/**
 * 格式化成交额
 * @param {number} amount
 * @param {object} options
 * @param {boolean} options.multiply 是否先将数值乘以 1000（某些接口返回千元）
 * @param {boolean} options.symbol 是否添加人民币符号
 * @returns {string}
 */
export function formatAmount(amount, { multiply = false, symbol = false } = {}) {
  if (!amount) return '-'
  let value = multiply ? amount * 1000 : amount
  const prefix = symbol ? '¥' : ''
  if (value >= 100000000) {
    return prefix + (value / 100000000).toFixed(2) + '亿'
  }
  if (value >= 10000) {
    return prefix + (value / 10000).toFixed(2) + '万'
  }
  return prefix + value.toFixed(0)
}

/**
 * 打开雪球网个股页面
 * @param {string | { ts_code: string }} source 股票代码或股票对象
 */
export function openXueqiu(source) {
  const tsCode = typeof source === 'string' ? source : source?.ts_code
  if (!tsCode) return
  const [code, exchange] = tsCode.split('.')
  if (!code || !exchange) return
  const xueqiuCode = exchange + code
  window.open(`https://xueqiu.com/S/${xueqiuCode}`, '_blank')
}

/**
 * 根据 ts_code 判断市场类型
 * @param {string} tsCode
 * @returns {string}
 */
export function getMarketType(tsCode) {
  if (!tsCode) return ''
  const [code, exchange] = tsCode.split('.')
  if (!code || !exchange) return ''
  const prefix = code.slice(0, 3)

  if (exchange === 'SH') {
    if (['600', '601', '603', '605'].includes(prefix)) return '主板'
    if (prefix === '688') return '科创板'
  } else if (exchange === 'SZ') {
    if (['000', '002'].includes(prefix)) return '主板'
    if (['300', '301'].includes(prefix)) return '创业板'
  } else if (exchange === 'BJ') {
    return '北交所'
  }
  return ''
}

/**
 * 格式化日期为 zh-CN 本地日期字符串
 * @param {string | Date} dateStr
 * @param {string} fallback 空值时的回退文本
 * @returns {string}
 */
export function formatDate(dateStr, fallback = '-') {
  if (!dateStr) return fallback
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

/**
 * 格式化日期时间为 YYYY-MM-DD HH:mm
 * @param {string | Date} dateStr
 * @param {string} fallback 空值时的回退文本
 * @returns {string}
 */
export function formatDateTime(dateStr, fallback = '-') {
  if (!dateStr) return fallback
  const d = new Date(dateStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/**
 * 格式化市值（tushare daily_basic total_mv 单位为万元，10000万 = 1亿）
 * @param {number} cap 市值（万元）
 * @param {string} fallback 空值时的回退文本
 * @returns {string}
 */
export function formatMarketCap(cap, fallback = '-') {
  if (!cap) return fallback
  return (cap / 10000).toFixed(2) + '亿'
}

/**
 * 根据信号类型返回 Element Plus tag 类型
 * @param {string} type
 * @returns {string}
 */
export function getSignalType(type) {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'info', NOTE: 'warning', ADD_TAG: '' }
  return map[type] || 'info'
}

/**
 * 根据信号类型返回时间线节点类型
 * @param {string} type
 * @returns {string}
 */
export function getSignalTimelineType(type) {
  const map = { BUY: 'success', SELL: 'danger', WATCH: 'primary', NOTE: 'warning', ADD_TAG: 'primary' }
  return map[type] || 'primary'
}

/**
 * 格式化信号类型为可读文案
 * @param {string} type
 * @returns {string}
 */
export function formatSignal(type) {
  const map = { BUY: '买入', SELL: '卖出', WATCH: '观望', NOTE: '备注', ADD_TAG: '添加标签' }
  return map[type] || type
}

/**
 * 根据市场类型返回 Element Plus tag 类型
 * @param {string} marketType
 * @returns {string}
 */
export function getMarketTypeTag(marketType) {
  switch (marketType) {
    case '主板':
      return 'primary'
    case '创业板':
      return 'success'
    case '科创板':
      return 'warning'
    case '北交所':
      return 'danger'
    default:
      return 'info'
  }
}
