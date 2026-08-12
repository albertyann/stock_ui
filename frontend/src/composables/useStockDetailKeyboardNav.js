import { onMounted, onUnmounted } from 'vue'
import { openXueqiu } from '@/utils/stock'

/**
 * 股票详情页键盘快捷键（Ctrl+X 前缀序列）：
 * - Ctrl+X -> O: 打开雪球
 * - Ctrl+X -> N: 打开备注弹窗
 * - Ctrl+X -> G: 打开标签编辑弹窗
 *
 * 与 useStockKeyboardNav（列表导航 j/k/h/l）语义不同，仅用于详情页。
 *
 * @param {object} options
 * @param {import('vue').Ref<object|null>} options.stock 当前股票
 * @param {import('vue').Ref<boolean>} options.showNotesDialog 备注弹窗可见性
 * @param {import('vue').Ref<boolean>} options.tagPopoverVisible 标签弹窗可见性
 * @param {() => void} options.openNotesDialog 打开备注弹窗
 * @param {() => void} options.openTagPopover 打开标签编辑弹窗
 */
export function useStockDetailKeyboardNav({ stock, showNotesDialog, tagPopoverVisible, openNotesDialog, openTagPopover }) {
  // Ctrl+X 按键序列状态
  let ctrlXPending = false
  let ctrlXTimer = null

  const handleKeydown = (e) => {
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
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
}
