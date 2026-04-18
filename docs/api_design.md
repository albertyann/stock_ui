# 股票关注系统 API 设计文档

## 基础信息
- **Base URL**: `/api/v1`
- **认证**: JWT Token (可选，支持多用户)
- **Content-Type**: `application/json`

---

## 1. 自选股分组 API

### 1.1 获取分组列表
```http
GET /watchlists
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "我的自选",
      "description": "默认分组",
      "is_default": true,
      "stock_count": 5,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 1.2 创建分组
```http
POST /watchlists
```

**Request Body**:
```json
{
  "name": "科技股",
  "description": "关注科技板块"
}
```

### 1.3 更新分组
```http
PUT /watchlists/{id}
```

### 1.4 删除分组
```http
DELETE /watchlists/{id}
```

---

## 2. 自选股管理 API

### 2.1 获取分组内股票
```http
GET /watchlists/{id}/stocks
```

**Response**:
```json
{
  "success": true,
  "data": {
    "watchlist_id": 1,
    "watchlist_name": "我的自选",
    "stocks": [
      {
        "id": 1,
        "ts_code": "000001.SZ",
        "symbol": "000001",
        "name": "平安银行",
        "added_at": "2024-01-15T10:30:00Z",
        "added_price": 12.50,
        "current_price": 13.20,
        "change_pct": 2.35,
        "return_pct": 5.60,
        "signal": {
          "type": "BUY",
          "strength": 4,
          "date": "2024-01-16"
        },
        "notes": "放量突破"
      }
    ]
  }
}
```

### 2.2 添加股票到分组
```http
POST /watchlists/{id}/stocks
```

**Request Body**:
```json
{
  "ts_code": "000001.SZ",
  "notes": "看好长期走势"
}
```

### 2.3 更新股票信息
```http
PUT /watchlists/{id}/stocks/{stock_id}
```

**Request Body**:
```json
{
  "notes": "更新备注",
  "alert_enabled": true
}
```

### 2.4 从分组移除股票
```http
DELETE /watchlists/{id}/stocks/{stock_id}
```

### 2.5 批量添加股票
```http
POST /watchlists/{id}/stocks/batch
```

**Request Body**:
```json
{
  "ts_codes": ["000001.SZ", "000002.SZ", "600000.SH"]
}
```

---

## 3. 买卖信号 API

### 3.1 获取信号列表
```http
GET /signals?type=BUY&active=true&limit=20
```

**Query Parameters**:
- `type`: 信号类型 (BUY/SELL/WATCH)
- `active`: 是否只显示有效信号
- `watchlist_id`: 指定分组
- `limit`: 返回数量限制
- `date_from`: 开始日期
- `date_to`: 结束日期

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "ts_code": "000001.SZ",
      "name": "平安银行",
      "signal_type": "BUY",
      "signal_strength": 4,
      "signal_date": "2024-01-16",
      "current_price": 13.20,
      "target_price": 15.00,
      "stop_loss_price": 12.00,
      "indicators": {
        "ma20": 12.80,
        "macd": 0.35,
        "kdj_j": 45,
        "rsi": 55
      },
      "strategy_name": "momentum",
      "conditions_met": 6,
      "is_active": true
    }
  ]
}
```

### 3.2 获取单只股票信号
```http
GET /stocks/{ts_code}/signals
```

### 3.3 手动触发信号分析
```http
POST /signals/analyze
```

**Request Body**:
```json
{
  "ts_codes": ["000001.SZ", "000002.SZ"],
  "strategies": ["momentum"]
}
```

### 3.4 标记信号已执行
```http
PUT /signals/{id}/execute
```

**Request Body**:
```json
{
  "execution_result": "已买入100股，成交价13.25"
}
```

---

## 4. 股票数据 API

### 4.1 搜索股票
```http
GET /stocks/search?q=平安
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "ts_code": "000001.SZ",
      "symbol": "000001",
      "name": "平安银行",
      "industry": "银行"
    }
  ]
}
```

### 4.2 获取股票详情
```http
GET /stocks/{ts_code}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "ts_code": "000001.SZ",
    "symbol": "000001",
    "name": "平安银行",
    "industry": "银行",
    "market": "主板",
    "current_price": 13.20,
    "change_pct": 2.35,
    "indicators": {
      "ma5": 12.90,
      "ma10": 12.75,
      "ma20": 12.80,
      "macd": 0.35,
      "kdj_k": 65,
      "kdj_d": 55,
      "kdj_j": 85,
      "rsi14": 55
    },
    "is_in_watchlist": true,
    "watchlist_count": 2
  }
}
```

### 4.3 获取K线数据
```http
GET /stocks/{ts_code}/kline?period=daily&limit=60
```

**Query Parameters**:
- `period`: 周期 (daily/weekly/monthly)
- `limit`: 返回条数
- `start_date`: 开始日期
- `end_date`: 结束日期

**Response**:
```json
{
  "success": true,
  "data": {
    "ts_code": "000001.SZ",
    "period": "daily",
    "data": [
      {
        "date": "2024-01-15",
        "open": 12.80,
        "high": 13.00,
        "low": 12.75,
        "close": 12.90,
        "volume": 1250000,
        "amount": 16125000
      }
    ]
  }
}
```

---

## 5. 技术指标 API

### 5.1 获取技术指标
```http
GET /stocks/{ts_code}/indicators
```

**Query Parameters**:
- `indicators`: 指标列表，逗号分隔 (ma,macd,kdj,rsi,boll)

**Response**:
```json
{
  "success": true,
  "data": {
    "ts_code": "000001.SZ",
    "trade_date": "2024-01-16",
    "ma": {
      "ma5": 12.90,
      "ma10": 12.75,
      "ma20": 12.80,
      "ma60": 12.50
    },
    "macd": {
      "dif": 0.35,
      "dea": 0.25,
      "bar": 0.20
    },
    "kdj": {
      "k": 65,
      "d": 55,
      "j": 85
    },
    "rsi": {
      "rsi6": 58,
      "rsi12": 55,
      "rsi24": 52
    }
  }
}
```

---

## 6. 实时数据 WebSocket (可选)

### 6.1 连接地址
```
ws://host:port/ws/stocks
```

### 6.2 订阅股票
```json
{
  "action": "subscribe",
  "ts_codes": ["000001.SZ", "000002.SZ"]
}
```

### 6.3 接收数据
```json
{
  "type": "price_update",
  "data": {
    "ts_code": "000001.SZ",
    "price": 13.25,
    "change_pct": 2.72,
    "volume": 1500000,
    "time": "2024-01-16T14:30:00Z"
  }
}
```

---

## 7. 仪表盘 API

### 7.1 获取仪表盘数据
```http
GET /dashboard
```

**Response**:
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_watchlists": 3,
      "total_stocks": 15,
      "buy_signals_count": 5,
      "sell_signals_count": 2
    },
    "recent_signals": [
      {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "signal_type": "BUY",
        "signal_strength": 4,
        "signal_date": "2024-01-16"
      }
    ],
    "top_performers": [
      {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "return_pct": 8.5
      }
    ]
  }
}
```

---

## 错误响应

**通用错误格式**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "股票代码格式不正确",
    "details": {
      "field": "ts_code",
      "value": "invalid"
    }
  }
}
```

**错误码列表**:
| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| INVALID_PARAMETER | 400 | 参数错误 |
| STOCK_NOT_FOUND | 404 | 股票不存在 |
| WATCHLIST_NOT_FOUND | 404 | 分组不存在 |
| ALREADY_EXISTS | 409 | 资源已存在 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
