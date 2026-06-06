"""Integration tests for market filter middleware."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.market.context import get_current_market
from app.market.middleware import MarketMiddleware

# Create a minimal app for testing (avoids importing main app which triggers DB init)
test_app = FastAPI()
test_app.add_middleware(MarketMiddleware)

@test_app.get("/test-market")
async def test_market(request: Request):
    return {"market": get_current_market()}

client = TestClient(test_app)


class TestMarketMiddleware:
    def test_middleware_with_hk_header(self):
        response = client.get("/test-market", headers={"X-Market": "HK"})
        assert response.status_code == 200
        assert response.json()["market"] == "HK"

    def test_middleware_without_header_defaults_to_a(self):
        response = client.get("/test-market")
        assert response.status_code == 200
        assert response.json()["market"] == "A"

    def test_middleware_with_invalid_header_defaults_to_a(self):
        response = client.get("/test-market", headers={"X-Market": "INVALID"})
        assert response.status_code == 200
        assert response.json()["market"] == "A"

    def test_middleware_does_not_break_requests(self):
        response = client.get("/test-market", headers={"X-Market": "HK"})
        assert response.status_code == 200
        response = client.get("/test-market")
        assert response.status_code == 200
        assert response.json()["market"] == "A"
