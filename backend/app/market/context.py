"""Market context variable for request-scoped market tracking."""

from contextvars import ContextVar, Token

MARKET_A = "A"
MARKET_HK = "HK"
VALID_MARKETS = {MARKET_A, MARKET_HK}

_current_market: ContextVar[str] = ContextVar("current_market", default=MARKET_A)


def get_current_market() -> str:
    """Get the current market from request context. Defaults to 'A'."""
    return _current_market.get()


def set_current_market(market: str) -> Token:
    """Set the current market in request context.

    Args:
        market: Market identifier ('A' or 'HK')

    Returns:
        Token for resetting the context variable later
    """
    if market not in VALID_MARKETS:
        market = MARKET_A
    return _current_market.set(market)


def reset_current_market(token: Token) -> None:
    """Reset the market context variable using the token from set_current_market."""
    _current_market.reset(token)
