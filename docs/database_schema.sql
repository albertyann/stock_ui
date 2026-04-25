-- =====================================================
-- 股票关注系统数据库设计 (PostgreSQL)
-- 数据库: stock_data
-- 连接: postgres://postgres:postgrespw@localhost:55000/stock_data
-- =====================================================

-- ============================================
-- 1. 自选股分组表
-- ============================================
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '分组名称，如"我的自选"、"科技股"',
    description TEXT COMMENT '分组描述',
    user_id VARCHAR(50) DEFAULT 'default' COMMENT '用户ID，支持多用户',
    is_default BOOLEAN DEFAULT FALSE COMMENT '是否默认分组',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

COMMENT ON TABLE watchlists IS '自选股分组表';

-- ============================================
-- 2. 自选股明细表 (关联股票)
-- ============================================
CREATE TABLE IF NOT EXISTS watchlist_stocks (
    id SERIAL PRIMARY KEY,
    watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码，如000001.SZ',
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码，如000001',
    name VARCHAR(100) COMMENT '股票名称',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_date VARCHAR(10) COMMENT '添加日期，格式 yyyy-MM-dd，用于日期搜索',
    added_price DECIMAL(10, 2) COMMENT '添加时的价格',
    notes TEXT COMMENT '备注',
    alert_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用提醒',
    UNIQUE(watchlist_id, ts_code)
);

COMMENT ON TABLE watchlist_stocks IS '自选股明细表';
CREATE INDEX idx_watchlist_stocks_code ON watchlist_stocks(ts_code);
CREATE INDEX idx_watchlist_stocks_watchlist ON watchlist_stocks(watchlist_id);
CREATE INDEX idx_watchlist_stocks_added_date ON watchlist_stocks(added_date);

-- ============================================
-- 3. 股票标签表 (全局标签，按 ts_code 存储)
-- ============================================
CREATE TABLE IF NOT EXISTS stock_tags (
    ts_code VARCHAR(20) PRIMARY KEY COMMENT '股票代码，如000001.SZ',
    tags JSONB DEFAULT '[]'::jsonb NOT NULL COMMENT '标签数组，如["白酒", "龙头"]',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stock_tags IS '股票标签表，支持全局标签管理';
CREATE INDEX idx_stock_tags_tags ON stock_tags USING GIN (tags);

-- ============================================
-- 4. 买卖信号表
-- ============================================
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    signal_type VARCHAR(20) NOT NULL COMMENT '信号类型: BUY(买入), SELL(卖出), WATCH(观望)',
    signal_strength INTEGER CHECK (signal_strength BETWEEN 1 AND 5) COMMENT '信号强度 1-5',
    signal_date DATE NOT NULL COMMENT '信号产生日期',
    
    -- 价格信息
    current_price DECIMAL(10, 2) COMMENT '当前价格',
    target_price DECIMAL(10, 2) COMMENT '目标价格',
    stop_loss_price DECIMAL(10, 2) COMMENT '止损价格',
    
    -- 技术指标摘要
    indicators JSONB COMMENT '相关技术指标数据: {"ma20": 10.5, "macd": 0.3, "kdj_j": 45}',
    
    -- 信号来源
    strategy_name VARCHAR(50) COMMENT '产生信号的策略名称',
    conditions_met INTEGER COMMENT '满足的条件数量',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    executed_at TIMESTAMP COMMENT '执行时间',
    execution_result TEXT COMMENT '执行结果备注',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE signals IS '买卖信号表';
CREATE INDEX idx_signals_code ON signals(ts_code);
CREATE INDEX idx_signals_type ON signals(signal_type);
CREATE INDEX idx_signals_date ON signals(signal_date);
CREATE INDEX idx_signals_active ON signals(is_active) WHERE is_active = TRUE;

-- ============================================
-- 4. 股票价格缓存表 (用于快速查询)
-- ============================================
CREATE TABLE IF NOT EXISTS stock_prices_cache (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2) NOT NULL,
    volume BIGINT,
    amount DECIMAL(15, 2),
    change_pct DECIMAL(6, 2) COMMENT '涨跌幅%',
    turnover_rate DECIMAL(6, 2) COMMENT '换手率%',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, trade_date)
);

COMMENT ON TABLE stock_prices_cache IS '股票价格缓存表';
CREATE INDEX idx_prices_code_date ON stock_prices_cache(ts_code, trade_date DESC);

-- ============================================
-- 5. 技术指标计算结果表
-- ============================================
CREATE TABLE IF NOT EXISTS technical_indicators_cache (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    
    -- 移动平均线
    ma5 DECIMAL(10, 4),
    ma10 DECIMAL(10, 4),
    ma20 DECIMAL(10, 4),
    ma60 DECIMAL(10, 4),
    
    -- MACD
    macd_dif DECIMAL(10, 4),
    macd_dea DECIMAL(10, 4),
    macd_bar DECIMAL(10, 4),
    
    -- KDJ
    kdj_k DECIMAL(6, 2),
    kdj_d DECIMAL(6, 2),
    kdj_j DECIMAL(6, 2),
    
    -- RSI
    rsi6 DECIMAL(6, 2),
    rsi12 DECIMAL(6, 2),
    rsi24 DECIMAL(6, 2),
    
    -- 布林带
    boll_upper DECIMAL(10, 4),
    boll_middle DECIMAL(10, 4),
    boll_lower DECIMAL(10, 4),
    
    -- 其他指标
    volume_ratio DECIMAL(6, 2) COMMENT '量比',
    amplitude DECIMAL(6, 2) COMMENT '振幅%',
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, trade_date)
);

COMMENT ON TABLE technical_indicators_cache IS '技术指标缓存表';
CREATE INDEX idx_indicators_code_date ON technical_indicators_cache(ts_code, trade_date DESC);

-- ============================================
-- 6. 股票信息表 (用户自定义备注)
-- ============================================
CREATE TABLE IF NOT EXISTS stock_info (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码，如000001.SZ',
    memo TEXT COMMENT '备注内容',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stock_info IS '股票信息备注表';
CREATE INDEX idx_stock_info_ts_code ON stock_info(ts_code);

-- ============================================
-- 7. 初始化数据
-- ============================================

-- 创建默认分组
INSERT INTO watchlists (name, description, user_id, is_default)
VALUES ('我的自选', '默认自选股分组', 'default', TRUE)
ON CONFLICT (user_id, name) DO NOTHING;

-- ============================================
-- 7. 触发器：自动更新 updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_watchlists_updated_at BEFORE UPDATE ON watchlists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signals_updated_at BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 8. 视图：活跃信号与股票信息聚合
-- ============================================
CREATE OR REPLACE VIEW v_active_signals AS
SELECT 
    s.*,
    ws.watchlist_id,
    w.name as watchlist_name,
    p.close_price as latest_price,
    p.change_pct as latest_change_pct
FROM signals s
LEFT JOIN watchlist_stocks ws ON s.ts_code = ws.ts_code
LEFT JOIN watchlists w ON ws.watchlist_id = w.id
LEFT JOIN LATERAL (
    SELECT close_price, change_pct 
    FROM stock_prices_cache 
    WHERE ts_code = s.ts_code 
    ORDER BY trade_date DESC 
    LIMIT 1
) p ON TRUE
WHERE s.is_active = TRUE
ORDER BY s.signal_date DESC, s.signal_strength DESC;

-- ============================================
-- 9. 视图：自选股完整信息
-- ============================================
CREATE OR REPLACE VIEW v_watchlist_details AS
SELECT 
    ws.id,
    ws.watchlist_id,
    w.name as watchlist_name,
    ws.ts_code,
    ws.symbol,
    ws.name as stock_name,
    ws.added_at,
    ws.added_price,
    ws.notes,
    ws.alert_enabled,
    p.close_price as current_price,
    p.change_pct,
    CASE 
        WHEN ws.added_price > 0 
        THEN ROUND(((p.close_price - ws.added_price) / ws.added_price * 100), 2)
        ELSE NULL 
    END as return_pct,
    s.signal_type,
    s.signal_strength,
    s.signal_date
FROM watchlist_stocks ws
JOIN watchlists w ON ws.watchlist_id = w.id
LEFT JOIN LATERAL (
    SELECT close_price, change_pct 
    FROM stock_prices_cache 
    WHERE ts_code = ws.ts_code 
    ORDER BY trade_date DESC 
    LIMIT 1
) p ON TRUE
LEFT JOIN LATERAL (
    SELECT signal_type, signal_strength, signal_date
    FROM signals
    WHERE ts_code = ws.ts_code AND is_active = TRUE
    ORDER BY signal_date DESC
    LIMIT 1
) s ON TRUE;

-- ============================================
-- 10. daily_data 表增加 updated_at 列
-- ============================================
ALTER TABLE daily_data
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now() NULL;
