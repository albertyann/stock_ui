from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
import logging

from app.auth.security import ACCESS_COOKIE, decode_token
from app.models import User
from app.websockets.manager import manager
from app.services.stock_service import StockService
from app.services.signal_service import SignalService
from app.database import async_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


async def _authenticate_ws(websocket: WebSocket, token: Optional[str]) -> User | None:
    raw = websocket.cookies.get(ACCESS_COOKIE) or token
    if not raw:
        return None
    try:
        payload = decode_token(raw)
    except Exception:
        return None
    if payload.get("type") != "access":
        return None
    try:
        async with async_session() as db:
            user = await db.get(User, int(payload["sub"]))
    except Exception:
        return None
    return user if (user and user.is_active) else None


@router.websocket("/stocks")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query("anonymous"),
    token: Optional[str] = Query(None),
):
    user = await _authenticate_ws(websocket, token)
    if not user:
        # 拒绝握手：浏览器会收到 4401 关闭码
        await websocket.close(code=4401)
        return
    client_id = f"{client_id}:{user.id}"

    await manager.connect(websocket, client_id)
    stock_service = StockService()

    try:
        await manager.send_personal_message(
            {"type": "connection", "status": "connected", "client_id": client_id},
            client_id,
        )

        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                action = message.get("action")

                if action == "subscribe":
                    ts_codes = message.get("ts_codes", [])
                    manager.subscribe(client_id, ts_codes)

                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "status": "success",
                            "subscribed": ts_codes,
                        },
                        client_id,
                    )

                    for ts_code in ts_codes:
                        detail = stock_service.get_stock_detail(ts_code)
                        if detail:
                            await manager.send_personal_message(
                                {
                                    "type": "price_update",
                                    "ts_code": ts_code,
                                    "data": {
                                        "price": detail.get("current_price"),
                                        "change_pct": detail.get("change_pct"),
                                        "volume": detail.get("volume"),
                                    },
                                },
                                client_id,
                            )

                elif action == "unsubscribe":
                    ts_codes = message.get("ts_codes", [])
                    manager.unsubscribe(client_id, ts_codes)

                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "status": "unsubscribed",
                            "unsubscribed": ts_codes,
                        },
                        client_id,
                    )

                elif action == "get_price":
                    ts_code = message.get("ts_code")
                    detail = stock_service.get_stock_detail(ts_code)
                    if detail:
                        await manager.send_personal_message(
                            {
                                "type": "price_update",
                                "ts_code": ts_code,
                                "data": {
                                    "price": detail.get("current_price"),
                                    "change_pct": detail.get("change_pct"),
                                    "volume": detail.get("volume"),
                                    "turnover_rate": detail.get("turnover_rate"),
                                },
                            },
                            client_id,
                        )

                elif action == "get_signal":
                    ts_code = message.get("ts_code")
                    async with async_session() as session:
                        signal_service = SignalService(session)
                        signal = await signal_service.get_latest_signal(ts_code)
                        if signal:
                            await manager.send_personal_message(
                                {
                                    "type": "signal",
                                    "ts_code": ts_code,
                                    "data": {
                                        "signal_type": signal.signal_type,
                                        "signal_strength": signal.signal_strength,
                                        "current_price": (
                                            float(signal.current_price)
                                            if signal.current_price
                                            else None
                                        ),
                                        "indicators": signal.indicators,
                                    },
                                },
                                client_id,
                            )

                elif action == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": message.get("timestamp")},
                        client_id,
                    )

                elif action == "get_stats":
                    stats = manager.get_stats()
                    await manager.send_personal_message(
                        {"type": "stats", "data": stats}, client_id
                    )

                else:
                    await manager.send_personal_message(
                        {"type": "error", "message": f"Unknown action: {action}"},
                        client_id,
                    )

            except WebSocketDisconnect:
                raise
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON format"}, client_id
                )
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {e}")
                await manager.send_personal_message(
                    {"type": "error", "message": str(e)}, client_id
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(websocket, client_id)


@router.get("/stats")
async def get_websocket_stats():
    return {"success": True, "data": manager.get_stats()}
