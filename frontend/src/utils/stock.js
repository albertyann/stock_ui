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
