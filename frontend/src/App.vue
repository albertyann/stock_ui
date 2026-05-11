<template>
  <div class="app-container">
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
          <el-sub-menu index="group-realtime">
            <template #title>
              <el-icon><DataLine /></el-icon>
              <span>实时股价</span>
            </template>
            <el-menu-item index="/realtime-price">
              <el-icon><TrendCharts /></el-icon>
              <span>实时股价</span>
            </el-menu-item>
            <el-menu-item index="/watchlist-stocks">
              <el-icon><Star /></el-icon>
              <span>关注清单</span>
            </el-menu-item>
            <el-menu-item index="/limit-up">
              <el-icon><TrendCharts /></el-icon>
              <span>今日涨停</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="group-tools">
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
          </el-sub-menu>
          <el-sub-menu index="group-analysis">
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
            <el-menu-item index="/sector-large-orders">
              <el-icon><Money /></el-icon>
              <span>板块大单</span>
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
          </el-sub-menu>
          <el-sub-menu index="group-basic-data">
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
          <el-sub-menu index="group-sync">
            <template #title>
              <el-icon><Refresh /></el-icon>
              <span>数据同步</span>
            </template>
            <el-menu-item index="/sync-tasks">
              <el-icon><Timer /></el-icon>
              <span>同步任务管理</span>
            </el-menu-item>
          </el-sub-menu>
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
            <i>{{ '一花一世界，一树一菩提' }}</i>
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
