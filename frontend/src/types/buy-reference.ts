/**
 * 买入参考模块类型定义
 * 
 * 核心概念：
 * - BuySignal: 买入信号，由策略生成
 * - Strategy: 策略接口，所有策略必须实现
 * - StrategyResult: 策略执行结果
 */

/**
 * 买入信号对象
 * 这是核心数据结构，包含完整的买入理由和策略信息
 */
export interface BuySignal {
  // 唯一标识
  id: string;
  
  // 股票信息
  stock: {
    tsCode: string;      // 股票代码，如 "000001.SZ"
    symbol: string;      // 股票代码，如 "000001"
    name: string;        // 股票名称
    exchange?: string;   // 交易所
  };
  
  // 策略信息
  strategy: {
    id: string;          // 策略ID
    name: string;        // 策略名称，如 "突破买入策略"
    type: StrategyType;  // 策略类型
    version?: string;    // 策略版本
  };
  
  // 信号强度 (0-100)
  strength: number;
  
  // 买入理由明细
  reasons: BuyReason[];
  
  // 技术指标数据
  indicators?: {
    ma5?: number;
    ma10?: number;
    ma20?: number;
    ma60?: number;
    rsi?: number;
    macd?: number;
    kdjK?: number;
    kdjD?: number;
    volumeRatio?: number;
    [key: string]: number | undefined;
  };
  
  // 建议买入价格区间
  priceRange?: {
    low: number;
    high: number;
    current: number;
  };
  
  // 止损价格
  stopLoss?: number;
  
  // 信号生成时间
  createdAt: Date;
  
  // 信号过期时间
  expireAt?: Date;
  
  // 信号状态
  status: SignalStatus;
  
  // 元数据
  metadata?: {
    marketCondition?: string;  // 市场环境
    sector?: string;           // 所属板块
    [key: string]: any;
  };
}

/**
 * 买入理由
 */
export interface BuyReason {
  // 理由类型
  type: ReasonType;
  
  // 理由标题
  title: string;
  
  // 详细描述
  description: string;
  
  // 相关指标
  indicator?: string;
  
  // 指标值
  value?: number | string;
  
  // 权重 (0-1)
  weight: number;
  
  // 是否满足
  satisfied: boolean;
}

/**
 * 策略类型
 */
export enum StrategyType {
  MOMENTUM = 'momentum',       // 动量策略
  BREAKOUT = 'breakout',       // 突破策略
  REVERSAL = 'reversal',       // 反转策略
  MEAN_REVERSION = 'mean_reversion', // 均值回归
  MULTI_FACTOR = 'multi_factor',     // 多因子策略
  TECHNICAL = 'technical',     // 技术形态
  FUNDAMENTAL = 'fundamental', // 基本面策略
  CUSTOM = 'custom'            // 自定义策略
}

/**
 * 理由类型
 */
export enum ReasonType {
  TREND = 'trend',           // 趋势
  VOLUME = 'volume',         // 成交量
  MOMENTUM = 'momentum',     // 动量
  SUPPORT_RESISTANCE = 'support_resistance', // 支撑阻力
  PATTERN = 'pattern',       // 形态
  INDICATOR = 'indicator',   // 指标
  FUNDAMENTAL = 'fundamental', // 基本面
  MARKET = 'market'          // 市场环境
}

/**
 * 信号状态
 */
export enum SignalStatus {
  ACTIVE = 'active',       // 活跃
  EXPIRED = 'expired',     // 过期
  EXECUTED = 'executed',   // 已执行
  CANCELLED = 'cancelled', // 已取消
  WATCHING = 'watching'    // 观察中
}

/**
 * 策略接口
 * 所有策略必须实现此接口
 */
export interface Strategy {
  // 策略ID
  id: string;
  
  // 策略名称
  name: string;
  
  // 策略类型
  type: StrategyType;
  
  // 策略版本
  version: string;
  
  // 策略描述
  description: string;
  
  // 执行策略
  execute(stockCode: string): Promise<StrategyResult>;
  
  // 批量执行
  executeBatch(stockCodes: string[]): Promise<StrategyResult[]>;
  
  // 获取策略参数
  getParameters(): StrategyParameter[];
  
  // 更新参数
  updateParameters(params: Record<string, any>): void;
}

/**
 * 策略执行结果
 */
export interface StrategyResult {
  // 策略信息
  strategy: {
    id: string;
    name: string;
    type: StrategyType;
  };
  
  // 是否产生信号
  hasSignal: boolean;
  
  // 信号详情（如果有）
  signal?: BuySignal;
  
  // 执行时间
  executedAt: Date;
  
  // 执行耗时(ms)
  duration: number;
  
  // 执行状态
  status: 'success' | 'error' | 'timeout';
  
  // 错误信息
  error?: string;
  
  // 原始数据
  rawData?: any;
}

/**
 * 策略参数
 */
export interface StrategyParameter {
  // 参数名
  name: string;
  
  // 参数类型
  type: 'number' | 'string' | 'boolean' | 'array';
  
  // 当前值
  value: any;
  
  // 默认值
  defaultValue: any;
  
  // 描述
  description: string;
  
  // 可选值（如果是枚举）
  options?: any[];
  
  // 数值范围（如果是number）
  min?: number;
  max?: number;
  step?: number;
}

/**
 * 策略管理器
 */
export interface StrategyManager {
  // 注册策略
  register(strategy: Strategy): void;
  
  // 获取策略
  getStrategy(id: string): Strategy | undefined;
  
  // 获取所有策略
  getAllStrategies(): Strategy[];
  
  // 按类型获取策略
  getStrategiesByType(type: StrategyType): Strategy[];
  
  // 执行所有策略
  executeAll(stockCodes: string[]): Promise<StrategyResult[]>;
  
  // 执行指定策略
  executeStrategy(strategyId: string, stockCodes: string[]): Promise<StrategyResult[]>;
}

/**
 * 买入信号过滤器
 */
export interface SignalFilter {
  // 策略类型
  strategyTypes?: StrategyType[];
  
  // 最小信号强度
  minStrength?: number;
  
  // 最大信号强度
  maxStrength?: number;
  
  // 信号状态
  status?: SignalStatus[];
  
  // 股票代码
  stockCodes?: string[];
  
  // 时间范围
  dateRange?: {
    start: Date;
    end: Date;
  };
  
  // 自定义过滤条件
  customFilter?: (signal: BuySignal) => boolean;
}

/**
 * 买入信号排序器
 */
export interface SignalSorter {
  // 排序字段
  field: 'strength' | 'createdAt' | 'strategy' | 'stock';
  
  // 排序方向
  direction: 'asc' | 'desc';
}

/**
 * 买入参考服务接口
 */
export interface BuyReferenceService {
  // 获取所有买入信号
  getSignals(filter?: SignalFilter, sorter?: SignalSorter): Promise<BuySignal[]>;
  
  // 获取单个信号
  getSignal(id: string): Promise<BuySignal | null>;
  
  // 执行策略生成新信号
  generateSignals(strategyIds?: string[]): Promise<StrategyResult[]>;
  
  // 将信号添加到观察池
  addToWatchlist(signalId: string, watchlistId: string): Promise<void>;
  
  // 从列表中移除信号
  removeSignal(id: string): Promise<void>;
  
  // 批量移除
  removeSignals(ids: string[]): Promise<void>;
  
  // 标记为已执行
  markAsExecuted(id: string): Promise<void>;
  
  // 获取策略列表
  getStrategies(): Strategy[];
  
  // 刷新信号
  refresh(): Promise<void>;
}

/**
 * 买入参考状态（用于状态管理）
 */
export interface BuyReferenceState {
  // 信号列表
  signals: BuySignal[];
  
  // 加载状态
  loading: boolean;
  
  // 当前过滤器
  filter: SignalFilter;
  
  // 当前排序
  sorter: SignalSorter;
  
  // 选中的信号
  selectedSignals: string[];
  
  // 最后更新时间
  lastUpdated: Date | null;
  
  // 错误信息
  error: string | null;
}
