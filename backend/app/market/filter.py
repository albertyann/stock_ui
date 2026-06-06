"""Market filter helpers for applying market isolation to database queries.

All filtering is based on ts_code suffixes:
- A-share (A): .SH, .SZ, .BJ
- HK (HK): .HK

We NEVER use stock_basic.market field because its values are ambiguous
(e.g. both A-shares and HK stocks can have market='主板').
"""

from typing import Any, Dict, List, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import InstrumentedAttribute

from app.market.context import MARKET_A, MARKET_HK


_A_SHARE_SUFFIXES = [".SH", ".SZ", ".BJ"]
_HK_SUFFIXES = [".HK"]


def get_market_ts_code_suffixes(market: str) -> List[str]:
    """Return list of ts_code suffixes for the given market.

    Args:
        market: 'A' or 'HK'

    Returns:
        List of suffix strings (e.g. ['.SH', '.SZ', '.BJ'] for A)
    """
    if market == MARKET_HK:
        return _HK_SUFFIXES.copy()
    return _A_SHARE_SUFFIXES.copy()


def build_sql_filter(market: str, ts_code_column: str = "ts_code") -> Tuple[str, Dict[str, Any]]:
    """Build SQL WHERE fragment and bind params for raw SQL queries.

    Args:
        market: 'A' or 'HK'
        ts_code_column: Column name or alias (e.g. 'ws.ts_code')

    Returns:
        Tuple of (sql_fragment, params_dict)
    """
    suffixes = get_market_ts_code_suffixes(market)
    conditions = []
    params: Dict[str, Any] = {}

    for i, suffix in enumerate(suffixes):
        param_name = f"market_suffix_{i}"
        conditions.append(f"{ts_code_column} LIKE :{param_name}")
        params[param_name] = f"%{suffix}"

    sql_fragment = "(" + " OR ".join(conditions) + ")"
    return sql_fragment, params


def build_orm_filter(market: str, model_column: InstrumentedAttribute) -> List[Any]:
    """Build SQLAlchemy ORM filter conditions.

    Args:
        market: 'A' or 'HK'
        model_column: SQLAlchemy model column attribute (e.g. WatchlistStock.ts_code)

    Returns:
        List of SQLAlchemy filter conditions (use with or_())
    """
    suffixes = get_market_ts_code_suffixes(market)
    return [model_column.like(f"%{suffix}") for suffix in suffixes]
