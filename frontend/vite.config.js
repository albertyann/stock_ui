import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// 后端地址可通过环境变量覆盖，默认沿用现有 :9000
// （注：AGENTS.md 记载为 :8000，若实际后端在 8000，请设置 .env: VITE_API_TARGET=http://localhost:8000）
const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:9000'

export default defineConfig({
  plugins: [
    vue(),
    // Element Plus 按需引入：
    //   - AutoImport：自动注入 ElMessage / ElMessageBox / ElNotification / ElLoading 等命令式 API
    //     （无需在 38 个 view 里手写 import { ElMessage } from 'element-plus'）
    //   - Components：模板里用到的 <el-xxx> 组件及其样式自动按需引入
    //   组合效果：element-vendor 从全量 ~1MB 降到仅含实际使用的组件
    AutoImport({
      resolvers: [ElementPlusResolver()]
    }),
    Components({
      resolvers: [ElementPlusResolver()]
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true
      },
      // WebSocket 代理（useWebSocket 连接 /ws/stocks）
      '/ws': {
        target: API_TARGET,
        changeOrigin: true,
        ws: true
      }
    }
  },
  build: {
    // 生产构建用 esbuild 进行 minify（vite 默认）
    sourcemap: false,
    // 大依赖拆分为独立 chunk，配合路由懒加载进一步减小首屏体积
    rollupOptions: {
      output: {
        manualChunks: {
          // Vue 运行时核心
          'vue-vendor': ['vue', 'vue-router', 'pinia']
        }
      }
    },
    // 提高警告阈值，避免因业务 chunk 自然变大而刷屏警告
    chunkSizeWarningLimit: 1000
  }
})
