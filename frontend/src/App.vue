<template>
  <router-view v-if="$route.meta.public" />
  <div v-else class="app-container">
    <el-container>
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <el-icon><TrendCharts /></el-icon>
          <span>小麦国度</span>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="el-menu-vertical"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-sub-menu index="group-realtime">
            <template #title>
              <el-icon><DataLine /></el-icon>
              <span>实时股价</span>
            </template>
            <el-menu-item index="/realtime-price">
              <el-icon><TrendCharts /></el-icon>
              <span>实时股价</span>
            </el-menu-item>
            <el-menu-item v-if="authStore.isAdmin" index="/watchlist-stocks">
              <el-icon><Star /></el-icon>
              <span>关注清单</span>
            </el-menu-item>
            <el-menu-item v-if="authStore.isAdmin" index="/watchlist-sector-stats">
              <el-icon><Grid /></el-icon>
              <span>关注板块</span>
            </el-menu-item>
            <el-menu-item v-if="authStore.isAdmin" index="/watchlist-sector-trend">
              <el-icon><TrendCharts /></el-icon>
              <span>板块趋势</span>
            </el-menu-item>
            <el-menu-item v-if="authStore.isAdmin" index="/limit-up">
              <el-icon><TrendCharts /></el-icon>
              <span>今日涨停</span>
            </el-menu-item>
            <el-menu-item v-if="authStore.isAdmin" index="/buy-point-query">
              <el-icon><Search /></el-icon>
              <span>买点查询</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu v-if="authStore.isAdmin" index="group-tools">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>股票工具</span>
            </template>
            <el-menu-item index="/stock-query">
              <el-icon><Search /></el-icon>
              <span>股票查询</span>
            </el-menu-item>
            <el-menu-item index="/stock-calculator">
              <el-icon><Coin /></el-icon>
              <span>股票计算器</span>
            </el-menu-item>
            <el-menu-item index="/moving-average-slope">
              <el-icon><TrendCharts /></el-icon>
              <span>均线斜率</span>
            </el-menu-item>
            <el-menu-item index="/indicator-calc">
              <el-icon><DataAnalysis /></el-icon>
              <span>指标计算</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu v-if="authStore.isAdmin" index="group-analysis">
            <template #title>
              <el-icon><TrendCharts /></el-icon>
              <span>分析工具</span>
            </template>
            <el-menu-item index="/sectors">
              <el-icon><Grid /></el-icon>
              <span>看板块</span>
            </el-menu-item>
            <el-menu-item index="/concept-sectors">
              <el-icon><Flag /></el-icon>
              <span>概念板块</span>
            </el-menu-item>
            <el-menu-item index="/sector-heat">
              <el-icon><TrendCharts /></el-icon>
              <span>板块热度</span>
            </el-menu-item>
            <el-menu-item index="/snapshot-manage">
              <el-icon><Camera /></el-icon>
              <span>快照管理</span>
            </el-menu-item>
            <el-menu-item index="/signal-manage">
              <el-icon><Bell /></el-icon>
              <span>信号管理</span>
            </el-menu-item>
            <el-menu-item index="/industry-daily-flow">
              <el-icon><Histogram /></el-icon>
              <span>行业每日净流入</span>
            </el-menu-item>
            <el-menu-item index="/incremental-industry">
              <el-icon><TrendCharts /></el-icon>
              <span>增量行业</span>
            </el-menu-item>
            <el-menu-item index="/hot-industries">
              <el-icon><Histogram /></el-icon>
              <span>火热行业</span>
            </el-menu-item>
            <el-menu-item index="/stock-fund-analysis">
              <el-icon><Money /></el-icon>
              <span>个股资金分析</span>
            </el-menu-item>
            <el-menu-item index="/daily-scores">
              <el-icon><Histogram /></el-icon>
              <span>每日量化评分</span>
            </el-menu-item>
            <el-menu-item index="/trading-heat">
              <el-icon><TrendCharts /></el-icon>
              <span>交易热度</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu v-if="authStore.isAdmin" index="group-basic-data">
            <template #title>
              <el-icon><DataLine /></el-icon>
              <span>基础数据</span>
            </template>
            <el-menu-item index="/basic-data/trade-cal">
              <el-icon><Calendar /></el-icon>
              <span>交易日历</span>
            </el-menu-item>
            <el-menu-item index="/basic-data/stocks">
              <el-icon><Document /></el-icon>
              <span>股票数据</span>
            </el-menu-item>
            <el-menu-item index="/basic-data/etfs">
              <el-icon><Coin /></el-icon>
              <span>ETF管理</span>
            </el-menu-item>
            <el-menu-item index="/basic-data/funds">
              <el-icon><Money /></el-icon>
              <span>基金管理</span>
            </el-menu-item>
            <el-menu-item index="/basic-data/index-basic">
              <el-icon><DataAnalysis /></el-icon>
              <span>指数管理</span>
            </el-menu-item>
            <el-menu-item index="/basic-data/daily">
              <el-icon><Histogram /></el-icon>
              <span>日线数据</span>
            </el-menu-item>
            <el-menu-item index="/basic-data/weekly">
              <el-icon><TrendCharts /></el-icon>
              <span>周线数据</span>
            </el-menu-item>
            <el-menu-item index="/basic-data/tags">
              <el-icon><PriceTag /></el-icon>
              <span>标签管理</span>
            </el-menu-item>
            <el-menu-item index="/basic-data/watchlists">
              <el-icon><Folder /></el-icon>
              <span>股票分组</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu v-if="authStore.isAdmin" index="group-sync">
            <template #title>
              <el-icon><Refresh /></el-icon>
              <span>数据同步</span>
            </template>
            <el-menu-item index="/sync-tasks">
              <el-icon><Timer /></el-icon>
              <span>股票同步</span>
            </el-menu-item>
            <el-menu-item index="/etf-sync">
              <el-icon><Coin /></el-icon>
              <span>ETF同步</span>
            </el-menu-item>
            <el-menu-item index="/index-sync">
              <el-icon><DataAnalysis /></el-icon>
              <span>指数同步</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu v-if="authStore.isAdmin" index="group-admin">
            <template #title>
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </template>
            <el-menu-item index="/admin/users">
              <el-icon><UserFilled /></el-icon>
              <span>用户列表</span>
            </el-menu-item>
          </el-sub-menu>
          <el-divider v-if="authStore.isAdmin" class="sidebar-divider" />
          <el-menu-item v-if="authStore.isAdmin" index="/settings">
            <el-icon><Setting /></el-icon>
            <span>设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="header-left">
            <i>{{ '一花一世界，一树一菩提' }}</i>
          </div>
          <div class="header-right">
            <MarketSwitcher />
            <el-dropdown v-if="authStore.isAuthenticated" trigger="click" @command="handleUserCommand">
              <span class="user-info">
                <el-icon><UserFilled /></el-icon>
                <span class="user-phone">{{ authStore.phone }}</span>
                <el-tag size="small" :type="authStore.isAdmin ? 'danger' : 'primary'">
                  {{ authStore.isAdmin ? '管理员' : '用户' }}
                </el-tag>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>

  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import MarketSwitcher from '@/components/MarketSwitcher.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

async function handleUserCommand(command) {
  if (command === 'logout') {
    await authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: var(--bg-sidebar);
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-subtle);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-display);
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.logo .el-icon {
  margin-right: 10px;
  font-size: 24px;
  color: var(--accent);
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;
}

.el-menu-vertical::-webkit-scrollbar {
  width: 6px;
}

.el-menu-vertical::-webkit-scrollbar-thumb {
  background-color: var(--border-subtle);
  border-radius: 3px;
}

.el-menu-vertical::-webkit-scrollbar-track {
  background-color: transparent;
}

/* Sub-menu items have less horizontal padding */
.el-menu-vertical :deep(.el-sub-menu__title),
.el-menu-vertical :deep(.el-menu-item) {
  border-radius: var(--radius-sm);
  margin: 2px 0;
  height: 44px;
  line-height: 44px;
}

/* Sidebar divider */
.sidebar-divider {
  margin: 10px 12px;
  border-color: var(--border-subtle);
  opacity: 0.5;
}

/* Main content area */
:deep(.el-main) {
  overflow-y: auto;
  height: calc(100vh - 60px);
  background: var(--bg-deep);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border-subtle);
  height: 60px;
  position: relative;
}

.header::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 70% 50%, rgba(16, 185, 129, 0.03), transparent 40%);
  pointer-events: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.header-left i {
  color: var(--text-muted);
  font-size: 14px;
  font-style: italic;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--text-primary);
  outline: none;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-input);
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.user-info:hover {
  border-color: var(--border-active);
  background: var(--bg-hover);
}

.user-phone {
  font-size: 14px;
  color: var(--text-primary);
}
</style>
