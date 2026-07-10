import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from '@/utils/echarts'

/**
 * Encapsulates the standard ECharts lifecycle for Vue 3 components.
 *
 * @param {object} options
 * @param {(instance: echarts.ECharts) => void} [options.onInit] - Called once after the chart is initialized.
 * @param {boolean} [options.autoResize=true] - Whether to call resize() on window resize.
 *
 * @returns {{
 *   chartRef: import('vue').Ref<HTMLElement | null>,
 *   chartInstance: import('vue').Ref<echarts.ECharts | null>,
 *   render: (option: object) => void,
 *   clear: () => void,
 *   resize: () => void,
 *   dispose: () => void
 * }}
 */
export function useECharts(options = {}) {
  const { onInit, autoResize = true } = options

  const chartRef = ref(null)
  const chartInstance = ref(null)

  const render = (option) => {
    if (!chartInstance.value || !option) return
    chartInstance.value.setOption(option, true)
  }

  const clear = () => {
    chartInstance.value?.clear()
  }

  const resize = () => {
    chartInstance.value?.resize()
  }

  const dispose = () => {
    if (chartInstance.value) {
      chartInstance.value.dispose()
      chartInstance.value = null
    }
  }

  onMounted(() => {
    if (!chartRef.value) return

    chartInstance.value = echarts.init(chartRef.value, 'dark-navy')

    if (onInit) {
      onInit(chartInstance.value)
    }

    if (autoResize) {
      window.addEventListener('resize', resize)
    }
  })

  onUnmounted(() => {
    if (autoResize) {
      window.removeEventListener('resize', resize)
    }
    dispose()
  })

  return {
    chartRef,
    chartInstance,
    render,
    clear,
    resize,
    dispose
  }
}
