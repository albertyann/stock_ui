import { ref } from 'vue'

// K 线图主图指标可见性默认值
const defaultKlineIndicatorSettings = {
  ma: { ma5: true, ma10: false, ma20: true, ma30: false, ma60: true, ma120: false },
  ema: { ema9: true, ema21: true },
  boll: false
}

const cloneIndicatorSettings = (settings) => JSON.parse(JSON.stringify(settings))

const loadSavedKlineIndicatorSettings = () => {
  try {
    const saved = localStorage.getItem('stockDetailKlineIndicators')
    if (saved) {
      const parsed = JSON.parse(saved)
      return {
        ma: { ...defaultKlineIndicatorSettings.ma, ...(parsed.ma || {}) },
        ema: { ...defaultKlineIndicatorSettings.ema, ...(parsed.ema || {}) },
        boll: parsed.boll ?? defaultKlineIndicatorSettings.boll
      }
    }
  } catch (error) {
    console.warn('Failed to load kline indicator settings:', error)
  }
  return cloneIndicatorSettings(defaultKlineIndicatorSettings)
}

/**
 * 日K主图指标（MA/EMA/BOLL）可见性设置，带 localStorage 持久化。
 * 弹窗的草稿/全选/重置逻辑由 KlineIndicatorDialog 组件内部处理，
 * 确认后通过 saveKlineIndicatorSettings(newSettings) 应用并持久化。
 *
 * @returns {{
 *   klineIndicatorSettings: import('vue').Ref<object>,
 *   saveKlineIndicatorSettings: (newSettings?: object) => void
 * }}
 */
export function useKlineIndicatorSettings() {
  const klineIndicatorSettings = ref(loadSavedKlineIndicatorSettings())

  const saveKlineIndicatorSettings = (newSettings) => {
    if (newSettings) {
      klineIndicatorSettings.value = newSettings
    }
    try {
      localStorage.setItem('stockDetailKlineIndicators', JSON.stringify(klineIndicatorSettings.value))
    } catch (error) {
      console.warn('Failed to save kline indicator settings:', error)
    }
  }

  return {
    klineIndicatorSettings,
    saveKlineIndicatorSettings
  }
}
