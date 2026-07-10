import { createApp } from 'vue'
import { createPinia } from 'pinia'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())

import { useMarketStore } from '@/stores/market'
import { useAuthStore } from '@/stores/auth'
const marketStore = useMarketStore()
marketStore.initMarket()

const authStore = useAuthStore()

app.use(router)

authStore.init().finally(() => {
  app.mount('#app')
})
