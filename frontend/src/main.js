import { createApp } from 'vue'
import { createPinia } from 'pinia'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
// 注：不再 app.use(ElementPlus) 与全量 CSS。
// 组件/样式由 vite.config.js 中 unplugin-vue-components + ElementPlusResolver 按需引入。

import App from './App.vue'
import router from './router'

const app = createApp(App)

// 图标仍全局注册（体积小、模板中按名字直接用，如 <TrendCharts />）
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())

import { useMarketStore } from '@/stores/market'
const marketStore = useMarketStore()
marketStore.initMarket()

app.use(router)

app.mount('#app')
