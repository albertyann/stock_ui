"""FastAPI middleware for extracting market from request headers."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.market.context import (
    MARKET_A,
    VALID_MARKETS,
    reset_current_market,
    set_current_market,
)


class MarketMiddleware(BaseHTTPMiddleware):
    """Middleware that reads X-Market header and sets request-scoped context variable.

    The market context is automatically reset after each request to prevent
    leakage between concurrent requests.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract market from header
        market = request.headers.get("X-Market", MARKET_A)

        # Validate
        if market not in VALID_MARKETS:
            market = MARKET_A

        # Set context variable and save token for reset
        token = set_current_market(market)

        try:
            response = await call_next(request)
        finally:
            # Always reset context to prevent leakage
            reset_current_market(token)

        return response
