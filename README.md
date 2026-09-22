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

### Docker 部署（推荐）

推荐使用 Docker Compose 一键启动，无需本地安装 Python、Node.js 和 PostgreSQL。

该栈包含两个服务：

- `redis` — Redis 7 (`redis:7-alpine`)，仅集群内部使用，不向宿主机发布端口
- `backend` — 由 `ui/backend/Dockerfile` 构建（多阶段：`node:20-alpine` 构建 Vue 前端 → `python:3.11-slim` 运行），镜像名为 `ui-backend`

后端不启动数据库，而是连接到一个已存在的 Postgres 容器（容器名为 `postgres`），该容器内已有真实的 `stock_data` 数据库（包含行情数据与用户）。连接方式为加入外部 Docker 网络 `trade-net`，并以容器名寻址数据库（`DB_HOST=postgres`）。

前端 SPA 由 FastAPI 直接提供，没有单独的前端容器，也不使用 nginx。`/api/*` 与 `/ws/*` 与页面同源同端口。

首次使用需先创建外部网络并把数据库容器接入（必须在 colima 上下文中执行，因为该数据库容器属于 colima）：

```bash
docker --context colima network create trade-net
docker --context colima network connect trade-net postgres
```

随后在 colima 上下文中启动本栈：

```bash
cd ui
docker --context colima compose up --build
```

也可以先把 colima 设为默认上下文，再直接运行：

```bash
docker context use colima
docker compose up --build
```

注意当前机器的活动上下文可能是 OrbStack，其守护进程并不包含该数据库容器，因此上下文的选择很重要。

启动后访问：

- http://localhost:9000/ — SPA 页面
- http://localhost:9000/docs — OpenAPI 文档
- http://localhost:9000/health — 健康检查
- http://localhost:9000/tasks/status — 定时任务状态
- ws://localhost:9000/ws/stocks — WebSocket

首次使用需在容器内创建管理员账号（会打印 TOTP 二维码）：

```bash
docker --context colima compose exec backend python scripts/create_admin.py --phone <phone>
```

可配置的 Compose 变量（可在 `ui/.env` 中设置或直接 export；默认值见 `ui/docker-compose.yml`）：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DB_HOST` | `postgres` | 数据库容器名 |
| `DB_PORT` | `5432` | 数据库端口 |
| `DB_NAME` | `stock_data` | 数据库名 |
| `DB_PASSWORD` | `postgrespwd` | PostgreSQL 密码 |
| `BACKEND_PORT` | `9000` | 后端服务端口 |
| `DEBUG` | `false` | 调试模式 |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT 密钥，生产环境必须修改 |
| `AI_API_KEY` | 空 | AI 接口密钥 |
| `TUSHARE_TOKEN` | 空 | Tushare 数据源令牌 |

注意事项：

1. `init_db()` 只会创建缺失的表；现有数据库已包含其表结构与数据，无需重新初始化或导入种子数据。
2. `DEBUG=false` 时要求 `JWT_SECRET_KEY` 非空。
3. 镜像内未打包同级的 `sync/` 与 `worker/` 模块，也未包含它们依赖的 macOS 绝对路径（`STOCK_SYNC_WORK_DIR`、`WORKER_WORK_DIR`、`STOCK_SYNC_CONFIG_PATH`），因此涉及外部调用的功能（数据同步任务、策略选股、个股评估、指标计算）在容器内不可用。

### 本地开发（可选）

如不使用 Docker，可按以下步骤在本地运行。

#### 1. 初始化数据库

```bash
python scripts/init_db.py
```

#### 2. 启动后端服务

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000
```

#### 3. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

#### 4. 访问应用

打开浏览器访问: http://localhost:6174

## API文档

启动后端后访问: http://localhost:9000/docs

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

查看任务状态: http://localhost:9000/tasks/status

## WebSocket实时推送

WebSocket地址: `ws://localhost:9000/ws/stocks`

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
