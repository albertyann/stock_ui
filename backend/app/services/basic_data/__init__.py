from app.services.basic_data._base import BasicDataServiceBase
from app.services.basic_data.trade_cal_service import TradeCalServiceMixin
from app.services.basic_data.stock_basic_service import StockBasicServiceMixin
from app.services.basic_data.market_data_service import MarketDataServiceMixin
from app.services.basic_data.moneyflow_service import MoneyflowServiceMixin
from app.services.basic_data.industry_moneyflow_service import IndustryMoneyflowServiceMixin
from app.services.basic_data.industry_analysis_service import IndustryAnalysisServiceMixin
from app.services.basic_data.cyq_chips_service import CyqChipsServiceMixin
from app.services.basic_data.sector_heat_service import SectorHeatServiceMixin
from app.services.basic_data.fina_audit_service import FinaAuditServiceMixin
from app.services.basic_data.fina_indicator_service import FinaIndicatorServiceMixin


class BasicDataService(
    BasicDataServiceBase,
    TradeCalServiceMixin,
    StockBasicServiceMixin,
    MarketDataServiceMixin,
    MoneyflowServiceMixin,
    IndustryMoneyflowServiceMixin,
    IndustryAnalysisServiceMixin,
    CyqChipsServiceMixin,
    SectorHeatServiceMixin,
    FinaAuditServiceMixin,
    FinaIndicatorServiceMixin,
):
    pass


__all__ = ["BasicDataService"]
