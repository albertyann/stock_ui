# 股票关注系统 - 实现规划文档

## 项目概述
基于现有A股智能选股系统，构建股票关注Web界面，支持添加自选股票、PostgreSQL数据存储、买卖信号提示。

---

## 一、项目结构

```
stock_watchlist/
├── backend/                      # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # PostgreSQL连接
│   │   ├── models/              # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── watchlist.py     # 自选股模型
│   │   │   ├── signal.py        # 信号模型
│   │   │   └── stock.py         # 股票模型
│   │   ├── routers/             # API路由
│   │   │   ├── __init__.py
│   │   │   ├── watchlists.py    # 自选股API
│   │   │   ├── signals.py       # 信号API
│   │   │   └── stocks.py        # 股票数据API
│   │   ├── services/            # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── watchlist_service.py
│   │   │   ├── signal_service.py
│   │   │   └── analysis_service.py
│   │   └── tasks/               # 定时任务
│   │       └── signal_analyzer.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── components/          # Vue组件
│   │   │   ├── Watchlist.vue
│   │   │   ├── StockCard.vue
│   │   │   ├── SignalBadge.vue
│   │   │   └── StockSearch.vue
│   │   ├── views/               # 页面
│   │   │   ├── Dashboard.vue
│   │   │   ├── WatchlistView.vue
│   │   │   └── StockDetail.vue
│   │   ├── stores/              # Pinia状态管理
│   │   │   ├── watchlist.js
│   │   │   └── signals.js
│   │   ├── api/                 # API客户端
│   │   │   └── index.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── docs/                        # 文档
│   ├── database_schema.sql
│   ├── api_design.md
│   └── implementation_plan.md   # 本文档
└── docker-compose.yml           # 部署配置
```

---

## 二、开发阶段规划

### Phase 1: 基础架构搭建（1-2天）

**目标**：搭建项目基础，数据库，基础配置

#### 1.1 环境准备
- [ ] 创建项目目录结构
- [ ] 初始化Python虚拟环境
- [ ] 初始化Vue项目
- [ ] 配置PostgreSQL连接

#### 1.2 数据库初始化
- [ ] 执行database_schema.sql创建表结构
- [ ] 创建初始数据（默认分组）
- [ ] 测试数据库连接

#### 1.3 后端基础
- [ ] 搭建FastAPI基础框架
- [ ] 配置PostgreSQL连接（使用asyncpg）
- [ ] 配置SQLAlchemy模型
- [ ] 设置CORS和基本中间件

#### 1.4 前端基础
- [ ] 配置Vue 3 + Vite
- [ ] 安装Element Plus
- [ ] 配置路由（Vue Router）
- [ ] 配置状态管理（Pinia）
- [ ] 配置HTTP客户端（Axios）

**交付物**：
- 可运行的后端服务
- 可运行的前端框架
- 初始化好的PostgreSQL数据库

---

### Phase 2: 后端核心功能开发（3-4天）

**目标**：完成后端API开发

#### 2.1 数据模型层
- [ ] 实现Watchlist模型（Pydantic + SQLAlchemy）
- [ ] 实现WatchlistStock模型
- [ ] 实现Signal模型
- [ ] 实现StockPriceCache模型
- [ ] 实现TechnicalIndicator模型

#### 2.2 自选股服务
- [ ] 创建WatchlistService类
- [ ] 实现创建分组
- [ ] 实现获取分组列表
- [ ] 实现添加股票到分组
- [ ] 实现从分组移除股票
- [ ] 实现批量添加
- [ ] 实现获取分组内股票详情（带价格、信号）

#### 2.3 股票数据服务
- [ ] 实现股票搜索功能
- [ ] 集成现有akshare数据获取
- [ ] 实现K线数据查询
- [ ] 实现价格缓存更新机制

#### 2.4 信号分析服务
- [ ] 创建SignalService类
- [ ] 集成现有momentum_strategy
- [ ] 实现技术指标计算（复用technical_indicators.py）
- [ ] 实现信号生成逻辑
- [ ] 实现信号存储到PostgreSQL
- [ ] 实现信号查询接口

#### 2.5 API路由层
- [ ] 实现Watchlist路由
- [ ] 实现Signals路由
- [ ] 实现Stocks路由
- [ ] 添加API文档（自动生成的Swagger）

**交付物**：
- 完整的REST API
- API文档
- 单元测试（可选）

---

### Phase 3: 前端界面开发（3-4天）

**目标**：完成用户界面

#### 3.1 基础布局
- [ ] 创建主布局组件（侧边栏 + 主内容区）
- [ ] 实现响应式设计
- [ ] 配置主题色（股票红绿配色）

#### 3.2 自选股管理界面
- [ ] 创建分组列表组件
- [ ] 创建添加分组对话框
- [ ] 创建股票列表组件
- [ ] 实现股票卡片（显示价格、涨跌幅、信号）
- [ ] 实现添加股票对话框（带搜索）
- [ ] 实现删除确认

#### 3.3 信号展示组件
- [ ] 创建信号徽章组件（买入/卖出/观望）
- [ ] 实现信号强度指示
- [ ] 实现信号详情弹窗

#### 3.4 股票详情页
- [ ] 创建股票信息卡片
- [ ] 集成K线图（ECharts）
- [ ] 显示技术指标
- [ ] 显示买卖信号历史

#### 3.5 仪表盘
- [ ] 创建统计数据卡片
- [ ] 显示最新信号列表
- [ ] 显示涨跌幅排行榜

**交付物**：
- 完整的前端界面
- 响应式设计
- 基础交互功能

---

### Phase 4: 信号分析引擎（2-3天）

**目标**：实现自动信号分析

#### 4.1 数据同步
- [ ] 创建定时任务获取最新行情
- [ ] 更新价格缓存表
- [ ] 更新技术指标缓存

#### 4.2 信号分析
- [ ] 实现批量信号分析（关注股票列表）
- [ ] 集成现有策略逻辑
- [ ] 生成买卖信号
- [ ] 存储信号到数据库

#### 4.3 实时更新（可选）
- [ ] 实现WebSocket服务器
- [ ] 推送价格更新
- [ ] 推送新信号通知

**交付物**：
- 自动信号分析功能
- 定时任务配置

---

### Phase 5: 集成与测试（1-2天）

**目标**：联调测试，修复问题

#### 5.1 端到端测试
- [ ] 测试添加自选股流程
- [ ] 测试信号显示
- [ ] 测试数据同步
- [ ] 测试各种边界情况

#### 5.2 性能优化
- [ ] 优化数据库查询（添加索引）
- [ ] 实现前端数据缓存
- [ ] 添加加载状态

#### 5.3 部署准备
- [ ] 编写Dockerfile
- [ ] 编写docker-compose.yml
- [ ] 编写部署文档

**交付物**：
- 可部署的应用
- 部署文档

---

## 三、关键技术实现要点

### 3.1 数据库连接配置

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:postgrespwd@localhost:5432/stock_data"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
```

### 3.2 信号生成服务

```python
# backend/app/services/signal_service.py
from stock_picker.strategy.momentum_strategy import MomentumStrategy
from stock_picker.analysis.technical_indicators import TechnicalIndicators

class SignalService:
    def __init__(self):
        self.momentum_strategy = MomentumStrategy()
        self.indicators = TechnicalIndicators()
    
    async def analyze_stock(self, ts_code: str, df: pd.DataFrame) -> dict:
        """分析单只股票并生成信号"""
        # 使用现有策略判断
        should_buy = self.momentum_strategy.should_buy(ts_code, df)
        
        if should_buy:
            return {
                "signal_type": "BUY",
                "strength": 4,
                "indicators": self._extract_indicators(df)
            }
        
        # 检查卖出信号
        should_sell = self.momentum_strategy.should_sell(ts_code, df, {})
        if should_sell:
            return {
                "signal_type": "SELL", 
                "strength": 3,
                "indicators": self._extract_indicators(df)
            }
        
        return {
            "signal_type": "WATCH",
            "strength": 0,
            "indicators": self._extract_indicators(df)
        }
```

### 3.3 前端状态管理

```javascript
// frontend/src/stores/watchlist.js
import { defineStore } from 'pinia'
import api from '@/api'

export const useWatchlistStore = defineStore('watchlist', {
  state: () => ({
    watchlists: [],
    currentWatchlist: null,
    stocks: [],
    loading: false
  }),
  
  actions: {
    async fetchWatchlists() {
      const response = await api.get('/watchlists')
      this.watchlists = response.data.data
    },
    
    async fetchStocks(watchlistId) {
      this.loading = true
      const response = await api.get(`/watchlists/${watchlistId}/stocks`)
      this.stocks = response.data.data.stocks
      this.loading = false
    },
    
    async addStock(watchlistId, tsCode) {
      await api.post(`/watchlists/${watchlistId}/stocks`, { ts_code: tsCode })
      await this.fetchStocks(watchlistId)
    }
  }
})
```

---

## 四、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 数据同步延迟 | 信号不准确 | 实现定时任务，每5分钟更新 |
| 股票代码格式不统一 | 数据查询失败 | 统一使用ts_code格式 |
| 前端性能问题 | 大量股票卡顿 | 实现虚拟滚动，分页加载 |
| 数据库连接池耗尽 | 服务不可用 | 配置连接池，添加重试机制 |
| 外部API限制 | 数据获取失败 | 实现降级方案，使用缓存数据 |

---

## 五、验收标准

### 功能验收
- [ ] 可以创建多个自选股分组
- [ ] 可以添加/删除自选股
- [ ] 可以搜索股票
- [ ] 自选股列表显示最新价格
- [ ] 自选股列表显示买卖信号
- [ ] 点击股票查看详情和K线
- [ ] 信号自动更新（定时任务）

### 性能验收
- [ ] 页面加载时间 < 2秒
- [ ] 股票列表滚动流畅（60fps）
- [ ] API响应时间 < 500ms
- [ ] 支持至少100只自选股流畅显示

### 质量验收
- [ ] 代码结构清晰，注释完整
- [ ] 错误处理完善
- [ ] 数据库连接正常关闭
- [ ] 无内存泄漏

---

## 六、后续优化方向

1. **实时推送**：WebSocket实现价格实时更新
2. **多用户支持**：JWT认证，用户隔离
3. **策略配置**：允许用户自定义信号策略参数
4. **通知系统**：信号产生时发送邮件/微信通知
5. **历史回测**：显示关注股票的历史信号表现
6. **移动端适配**：开发移动端H5或小程序
7. **数据可视化**：更丰富的图表分析

---

**预计总工期**：10-15天（单人开发）
**建议团队配置**：1后端 + 1前端，可缩短至5-7天
