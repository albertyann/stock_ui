from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_connections: Dict[str, List[WebSocket]] = {}
            cls._instance.user_subscriptions: Dict[str, Set[str]] = {}
        return cls._instance

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()

        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

        if client_id not in self.user_subscriptions:
            self.user_subscriptions[client_id] = set()

        logger.info(
            f"Client {client_id} connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)

            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
                if client_id in self.user_subscriptions:
                    del self.user_subscriptions[client_id]

        logger.info(f"Client {client_id} disconnected")

    def subscribe(self, client_id: str, ts_codes: List[str]):
        if client_id in self.user_subscriptions:
            self.user_subscriptions[client_id].update(ts_codes)
            logger.info(f"Client {client_id} subscribed to: {ts_codes}")

    def unsubscribe(self, client_id: str, ts_codes: List[str]):
        if client_id in self.user_subscriptions:
            self.user_subscriptions[client_id].difference_update(ts_codes)
            logger.info(f"Client {client_id} unsubscribed from: {ts_codes}")

    async def broadcast_to_subscribers(self, ts_code: str, message: dict):
        message["timestamp"] = datetime.now().isoformat()

        disconnected_clients = []

        for client_id, subscriptions in self.user_subscriptions.items():
            if ts_code in subscriptions or "*" in subscriptions:
                if client_id in self.active_connections:
                    for connection in self.active_connections[client_id]:
                        try:
                            await connection.send_json(message)
                        except Exception as e:
                            logger.error(f"Error sending to client {client_id}: {e}")
                            disconnected_clients.append((client_id, connection))

        for client_id, connection in disconnected_clients:
            self.disconnect(connection, client_id)

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            message["timestamp"] = datetime.now().isoformat()
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending personal message to {client_id}: {e}")

    async def broadcast(self, message: dict):
        message["timestamp"] = datetime.now().isoformat()
        disconnected_clients = []

        for client_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {e}")
                    disconnected_clients.append((client_id, connection))

        for client_id, connection in disconnected_clients:
            self.disconnect(connection, client_id)

    def get_stats(self):
        total_connections = sum(
            len(conns) for conns in self.active_connections.values()
        )
        return {
            "active_clients": len(self.active_connections),
            "total_connections": total_connections,
            "subscriptions": {
                client_id: list(subs)
                for client_id, subs in self.user_subscriptions.items()
            },
        }


manager = ConnectionManager()


async def broadcast_price_update(ts_code: str, price_data: dict):
    await manager.broadcast_to_subscribers(
        ts_code, {"type": "price_update", "ts_code": ts_code, "data": price_data}
    )


async def broadcast_signal(signal_data: dict):
    await manager.broadcast_to_subscribers(
        signal_data.get("ts_code", "*"), {"type": "new_signal", "data": signal_data}
    )


async def broadcast_system_message(message: str, level: str = "info"):
    await manager.broadcast({"type": "system", "level": level, "message": message})


async def broadcast_notes_updated(ts_code: str, notes: str):
    await manager.broadcast({
        "type": "notes_updated",
        "ts_code": ts_code,
        "notes": notes,
    })
