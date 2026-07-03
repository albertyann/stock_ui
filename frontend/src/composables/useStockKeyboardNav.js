import { ref, onMounted, onUnmounted, nextTick } from 'vue'

/**
 * 可复用的股票列表键盘导航组合式函数。
 *
 * 支持：
 * - Ctrl+x 前缀键
 * - j/k 上下移动选中项
 * - h/l 翻页（可选）
 * - Ctrl+x+o 打开雪球
 * - Ctrl+x+s 加入关注（可选）
 * - 自动滚动到选中的股票卡片
 *
 * @param {object} options
 * @param {import('vue').Ref<Array>} options.items 当前列表数据
 * @param {import('vue').Ref<number>} options.selectedIndex 当前选中索引
 * @param {(item: any, index: number) => void} [options.onSelect] 选中项变化时的回调
 * @param {(item: any) => void} options.openXueqiu 打开雪球的回调
 * @param {(item: any) => void} [options.addToWatchlist] 加入关注的回调
 * @param {object} [options.pageTurn] 翻页配置
 * @param {import('vue').Ref<number>} options.pageTurn.currentPage 当前页
 * @param {import('vue').Ref<number>} options.pageTurn.pageSize 每页条数
 * @param {import('vue').Ref<number>} options.pageTurn.totalItems 总条数
 * @param {(page: number, skipScroll?: boolean) => void} options.pageTurn.onPageChange 翻页回调
 * @param {string | false} [options.scrollSelector='.stock-card'] 滚动目标选择器，传 false 禁用
 */
export function useStockKeyboardNav(options) {
  const { items, selectedIndex, onSelect, openXueqiu, addToWatchlist, pageTurn, scrollSelector = '.stock-card' } = options

  const ctrlXPressed = ref(false)

  const isInputTarget = (target) => {
    const tagName = target?.tagName
    return tagName === 'INPUT' || tagName === 'TEXTAREA' || target?.isContentEditable
  }

  const scrollToSelected = () => {
    if (scrollSelector === false) return
    nextTick(() => {
      const elements = document.querySelectorAll(scrollSelector)
      const el = elements[selectedIndex.value]
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    })
  }

  const moveSelection = (delta) => {
    const maxIndex = items.value.length - 1
    const newIndex = selectedIndex.value + delta
    if (newIndex < 0 || newIndex > maxIndex) return

    selectedIndex.value = newIndex
    const item = items.value[newIndex]
    if (onSelect) {
      onSelect(item, newIndex)
    }
    scrollToSelected()
  }

  const turnPage = (delta) => {
    if (!pageTurn) return
    const totalPages = Math.ceil(pageTurn.totalItems.value / pageTurn.pageSize.value)
    const newPage = pageTurn.currentPage.value + delta
    if (newPage < 1 || newPage > totalPages) return

    pageTurn.onPageChange(newPage, true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleKeydown = (event) => {
    if (isInputTarget(event.target)) return

    const maxIndex = items.value.length - 1

    if (event.ctrlKey && event.key === 'x') {
      event.preventDefault()
      ctrlXPressed.value = true
      return
    }

    if (ctrlXPressed.value) {
      ctrlXPressed.value = false

      if (event.key === 'o') {
        event.preventDefault()
        const selectedStock = items.value[selectedIndex.value]
        if (selectedStock) {
          openXueqiu(selectedStock)
        }
        return
      }

      if (event.key === 's' && addToWatchlist) {
        event.preventDefault()
        const selectedStock = items.value[selectedIndex.value]
        if (selectedStock) {
          addToWatchlist(selectedStock)
        }
        return
      }
    }

    if (event.key === 'j') {
      event.preventDefault()
      if (selectedIndex.value < maxIndex) {
        moveSelection(1)
      }
    } else if (event.key === 'k') {
      event.preventDefault()
      if (selectedIndex.value > 0) {
        moveSelection(-1)
      }
    } else if (event.key === 'l') {
      event.preventDefault()
      turnPage(1)
    } else if (event.key === 'h') {
      event.preventDefault()
      turnPage(-1)
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
}
