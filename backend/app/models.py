from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Numeric,
    Date,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    user_id = Column(String(50), default="default")
    is_default = Column(Boolean, default=False)
    sort_num = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    stocks = relationship(
        "WatchlistStock", back_populates="watchlist", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uix_user_watchlist_name"),
    )


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"))
    ts_code = Column(String(20), nullable=False, index=True)
    symbol = Column(String(10), nullable=False)
    name = Column(String(100))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    watch_date = Column(
        String(10), index=True
    )  # 关注日期，格式 yyyy-MM-dd，用于日期搜索
    watch_reason = Column(String(50))  # 关注原因
    added_price = Column(Numeric(10, 2))
    notes = Column(Text)
    alert_enabled = Column(Boolean, default=True)
    status = Column(Integer, default=1)  # 1=热点(hot), 2=静默(silent)

    watchlist = relationship("Watchlist", back_populates="stocks")

    __table_args__ = (
        UniqueConstraint("watchlist_id", "ts_code", name="uix_watchlist_stock"),
    )


class StockTag(Base):
    __tablename__ = "stock_tags"

    ts_code = Column(String(20), primary_key=True)
    tags = Column(JSONB, default=list, server_default="[]")
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)
    signal_strength = Column(Integer)
    signal_date = Column(Date, nullable=False)
    current_price = Column(Numeric(10, 2))
    target_price = Column(Numeric(10, 2))
    stop_loss_price = Column(Numeric(10, 2))
    indicators = Column(JSONB)
    strategy_name = Column(String(50))
    conditions_met = Column(Integer)
    is_active = Column(Boolean, default=True)
    executed_at = Column(DateTime(timezone=True))
    execution_result = Column(Text)
    note_content = Column(Text)  # 用于记录 NOTE 类型的备注内容
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StockPriceCache(Base):
    __tablename__ = "stock_prices_cache"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    open_price = Column(Numeric(10, 2))
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    close_price = Column(Numeric(10, 2), nullable=False)
    volume = Column(Integer)
    amount = Column(Numeric(15, 2))
    change_pct = Column(Numeric(6, 2))
    turnover_rate = Column(Numeric(6, 2))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uix_stock_price_date"),
    )


class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators_cache"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    ma5 = Column(Numeric(10, 4))
    ma10 = Column(Numeric(10, 4))
    ma20 = Column(Numeric(10, 4))
    ma60 = Column(Numeric(10, 4))
    macd_dif = Column(Numeric(10, 4))
    macd_dea = Column(Numeric(10, 4))
    macd_bar = Column(Numeric(10, 4))
    kdj_k = Column(Numeric(6, 2))
    kdj_d = Column(Numeric(6, 2))
    kdj_j = Column(Numeric(6, 2))
    rsi6 = Column(Numeric(6, 2))
    rsi12 = Column(Numeric(6, 2))
    rsi24 = Column(Numeric(6, 2))
    boll_upper = Column(Numeric(10, 4))
    boll_middle = Column(Numeric(10, 4))
    boll_lower = Column(Numeric(10, 4))
    volume_ratio = Column(Numeric(6, 2))
    amplitude = Column(Numeric(6, 2))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uix_indicator_date"),
    )


class TradeCal(Base):
    __tablename__ = "trade_cal"

    exchange = Column(String(10), primary_key=True)
    cal_date = Column(Date, primary_key=True)
    is_open = Column(Integer)
    pretrade_date = Column(Date)


class StockBasic(Base):
    __tablename__ = "stock_basic"

    ts_code = Column(String(20), primary_key=True)
    symbol = Column(String(10))
    name = Column(String(100))
    industry = Column(String(50))
    market = Column(String(20))
    list_date = Column(Date)
    update_time = Column(DateTime(timezone=False), nullable=False)


class DailyData(Base):
    __tablename__ = "daily_data"

    ts_code = Column(String(20), primary_key=True)
    trade_date = Column(Date, primary_key=True)
    open = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    pre_close = Column(Numeric(10, 2))
    change = Column(Numeric(10, 2))
    pct_chg = Column(Numeric(10, 2))
    vol = Column(Numeric(15, 2))
    amount = Column(Numeric(15, 2))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WeeklyData(Base):
    __tablename__ = "weekly_data"

    ts_code = Column(String(20), primary_key=True)
    trade_date = Column(Date, primary_key=True)
    open = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    pre_close = Column(Numeric(10, 2))
    change = Column(Numeric(10, 2))
    pct_chg = Column(Numeric(10, 2))
    vol = Column(Numeric(15, 2))
    amount = Column(Numeric(15, 2))


class WatchlistSnapshot(Base):
    __tablename__ = "watchlist_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(
        Integer,
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_date = Column(String(10), nullable=False, index=True)
    snapshot_time = Column(String(8), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship(
        "WatchlistSnapshotItem", back_populates="snapshot", cascade="all, delete-orphan"
    )


class WatchlistSnapshotItem(Base):
    __tablename__ = "watchlist_snapshot_items"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(
        Integer,
        ForeignKey("watchlist_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ts_code = Column(String(20), nullable=False, index=True)
    name = Column(String(100))
    industry = Column(String(50))
    notes = Column(Text)

    snapshot = relationship("WatchlistSnapshot", back_populates="items")


class SyncTask(Base):
    __tablename__ = "sync_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    command = Column(String(50), default="stock-sync")
    sub_command = Column(String(50), default="run")
    task_type = Column(String(50), nullable=False)
    params = Column(JSONB, default=dict)
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SyncTaskLog(Base):
    __tablename__ = "sync_task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Numeric)
    records_processed = Column(Integer, server_default="0")
    records_inserted = Column(Integer, server_default="0")
    records_updated = Column(Integer, server_default="0")
    error_message = Column(Text)
    stack_trace = Column(Text)
    retry_count = Column(Integer, server_default="0")
    trigger_type = Column(String(20), server_default="scheduled")
    triggered_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StockInfo(Base):
    __tablename__ = "stock_info"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), nullable=False, index=True)
    memo = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
