<template>
  <div class="app-container">
    <el-container>
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <el-icon><TrendCharts /></el-icon>
          <span>股票关注</span>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="el-menu-vertical"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/buy-reference">
            <el-icon><TrendCharts /></el-icon>
            <span>买入参考</span>
          </el-menu-item>
          <el-menu-item index="/realtime-price">
            <el-icon><DataLine /></el-icon>
            <span>实时股价</span>
          </el-menu-item>
          <el-menu-item index="/sectors">
            <el-icon><Grid /></el-icon>
            <span>看板块</span>
          </el-menu-item>
          <el-menu-item index="/limit-up">
            <el-icon><TrendCharts /></el-icon>
            <span>今日涨停</span>
          </el-menu-item>
          <el-menu-item index="/stock-query">
            <el-icon><Search /></el-icon>
            <span>股票查询</span>
          </el-menu-item>
          <el-menu-item 
            v-for="wl in watchlists" 
            :key="wl.id" 
            :index="`/watchlist/${wl.id}`"
          >
            <el-icon><Folder /></el-icon>
            <span>{{ wl.name }}</span>
          </el-menu-item>
          <el-divider class="sidebar-divider" />
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <h2>{{ $route.meta.title || '股票关注系统' }}</h2>
          </div>
          <div class="header-right">
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>新建分组
            </el-button>
          </div>
        </el-header>
        
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <el-dialog v-model="showCreateDialog" title="新建分组" width="400px">
      <el-form :model="newWatchlist" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="newWatchlist.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="newWatchlist.description" 
            type="textarea" 
            placeholder="请输入描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createWatchlist">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { storeToRefs } from 'pinia'

const store = useWatchlistStore()
const { watchlists } = storeToRefs(store)

const showCreateDialog = ref(false)
const newWatchlist = ref({ name: '', description: '' })

onMounted(() => {
  store.fetchWatchlists()
})

const createWatchlist = async () => {
  if (!newWatchlist.value.name.trim()) {
    return
  }
  try {
    await store.createWatchlist(newWatchlist.value)
    showCreateDialog.value = false
    newWatchlist.value = { name: '', description: '' }
  } catch (error) {
    console.error('Failed to create watchlist:', error)
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  color: white;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
  flex-shrink: 0;
}

.logo .el-icon {
  margin-right: 10px;
  font-size: 24px;
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 自定义滚动条样式 */
.el-menu-vertical::-webkit-scrollbar {
  width: 6px;
}

.el-menu-vertical::-webkit-scrollbar-thumb {
  background-color: #1f2d3d;
  border-radius: 3px;
}

.el-menu-vertical::-webkit-scrollbar-track {
  background-color: #304156;
}

/* 侧边栏分割线样式 */
.sidebar-divider {
  margin: 10px 20px;
  border-color: #1f2d3d;
  opacity: 0.5;
}

/* 主内容区域样式 */
:deep(.el-main) {
  overflow-y: auto;
  height: calc(100vh - 60px);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.el-menu-vertical {
  border-right: none;
}
</style>
