# 股票关注系统 (Stock Watchlist System)

基于 FastAPI + Vue 3 + PostgreSQL 的股票关注Web界面，支持添加自选股票、买卖信号提示。

## 功能特性

- ✅ 多分组自选股管理
- ✅ 股票搜索与添加
- ✅ 自动买卖信号分析（基于启动初期策略）
- ✅ 实时价格显示
- ✅ K线图展示
- ✅ PostgreSQL数据存储
- ✅ 定时任务（自动信号分析、价格缓存更新）
- ✅ WebSocket实时推送（价格更新、新信号）
- ✅ 实时监控面板

## 项目结构

```
stock_watchlist/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── models.py       # 数据模型
│   │   ├── routers/        # API路由
│   │   ├── services/       # 业务逻辑
│   │   ├── tasks/          # 定时任务
│   │   │   └── scheduler.py
│   │   ├── websockets/     # WebSocket管理
│   │   │   ├── manager.py
│   │   │   └── routes.py
│   │   ├── database.py     # 数据库连接
│   │   └── main.py         # 应用入口
│   └── requirements.txt
├── frontend/               # Vue 3前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── stores/         # Pinia状态管理
│   │   ├── api/            # API客户端
│   │   ├── router/         # 路由配置
│   │   └── composables/    # Vue组合式函数
│   │       └── useWebSocket.js
│   └── package.json
├── docs/                   # 设计文档
└── scripts/                # 工具脚本
```

## 快速开始

### 1. 初始化数据库

```bash
cd stock_watchlist
python scripts/init_db.py
```

### 2. 启动后端服务

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd app
uvicorn main:app --reload --port 8000
```

### 3. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问应用

打开浏览器访问: http://localhost:5173

## API文档

启动后端后访问: http://localhost:8000/docs

## 定时任务

系统内置3个定时任务：

1. **信号分析任务** (每10分钟)
   - 自动分析所有关注股票
   - 生成买卖信号
   - 保存到数据库

2. **价格缓存更新** (每5分钟)
   - 更新所有关注股票的最新价格
   - 缓存到数据库
   - 通过WebSocket推送

3. **信号清理任务** (每天凌晨2点)
   - 清理30天前的非活跃信号
   - 保持数据库性能

查看任务状态: http://localhost:8000/tasks/status

## WebSocket实时推送

WebSocket地址: `ws://localhost:8000/ws/stocks`

支持的消息类型：
- `subscribe` - 订阅股票
- `unsubscribe` - 取消订阅
- `get_price` - 获取实时价格
- `get_signal` - 获取最新信号
- `ping/pong` - 心跳检测

推送数据类型：
- `price_update` - 价格更新
- `new_signal` - 新信号
- `system` - 系统消息

## 技术栈

- **后端**: FastAPI, SQLAlchemy, asyncpg, pandas
- **前端**: Vue 3, Element Plus, ECharts, Pinia
- **数据库**: PostgreSQL
- **数据源**: akshare (A股数据)

## 买卖信号策略

系统使用现有的`momentum_strategy`策略：

**买入信号**:
- 收盘价处于20日均线以上
- 20日均线方向向上
- 成交量 > 过去5日均量 × 1.3
- KDJ J值 < 100
- 换手率 3%-18%
- 3日涨幅 3%-12%

**卖出信号**:
- 收盘价跌破20日均线
- 从买入价回撤超过5%
- 3日涨幅超过20%
- KDJ J值超过100且开始下降

## 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

## 许可证

MIT
