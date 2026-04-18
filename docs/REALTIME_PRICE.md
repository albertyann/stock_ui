# 实时股价模块

## 功能说明

新增实时股价查询模块，支持通过 Tushare rt_k 接口获取 A 股实时行情数据。

## 后端配置

### 1. 环境变量配置

在 `backend/.env` 文件中添加 Tushare Token：

```env
TUSHARE_TOKEN=your_tushare_token_here
```

获取 Token：
- 访问 [Tushare Pro](https://tushare.pro/)
- 注册账号并获取个人 Token
- rt_k 接口需要单独申请权限

### 2. API 端点

- `POST /api/v1/realtime/prices` - 获取实时股价
  - 请求体: `{ "ts_codes": "600000.SH,000001.SZ" }`
  - 支持逗号或换行分隔的股票代码

- `POST /api/v1/realtime/refresh` - 刷新指定股票价格
  - 请求体: `{ "ts_codes": ["600000.SH", "000001.SZ"] }`

- `GET /api/v1/realtime/health` - 服务健康检查

## 前端功能

### 1. 页面入口

- 侧边栏导航：实时股价
- 仪表盘快捷入口：实时股价卡片

### 2. 功能特性

- 支持逗号或换行分隔输入股票代码
- 自动识别股票代码交易所（6开头=上海，0/3开头=深圳）
- 实时显示：当前价、涨跌幅、开盘价、最高最低价、成交量额
- 盘口数据：买一卖一价格
- 统计卡片：上涨/下跌/平盘数量统计
- 股票卡片采用颜色区分涨跌（红色=涨，绿色=跌）
- 支持跳转到股票详情页

### 3. 输入示例

```
600000.SH, 000001.SZ
300001.SZ
600000
000001
300001
```

## 文件变更

### 新增文件

- `backend/app/services/realtime_service.py` - 实时股价服务
- `backend/app/routers/realtime.py` - API 路由
- `frontend/src/views/RealtimePrice.vue` - 前端页面

### 修改文件

- `backend/app/config.py` - 添加 tushare_token 配置
- `backend/app/main.py` - 注册 realtime 路由
- `frontend/src/api/index.js` - 添加 realtimeApi
- `frontend/src/router/index.js` - 添加实时股价路由
- `frontend/src/App.vue` - 添加导航菜单项
- `frontend/src/views/Dashboard.vue` - 添加快捷入口

## 启动服务

```bash
# 启动后端
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 启动前端
cd frontend
npm run dev
```

## 依赖

- httpx (已包含在 requirements.txt)
- Tushare Pro 账号及 rt_k 接口权限
