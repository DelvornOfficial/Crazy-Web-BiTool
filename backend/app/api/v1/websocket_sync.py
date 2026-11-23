import asyncio
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("nextlevelcheat.ws")

router = APIRouter(prefix="/ws", tags=["Realtime Sync WebSocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: dict = None):
        """
        Broadcast live update events to all connected frontend & admin clients.
        Events: 'CONFIG_UPDATED', 'RELEASE_UPDATED', 'VIDEOS_UPDATED', 'FEATURES_UPDATED', 'FAQS_UPDATED'
        """
        if not self.active_connections:
            return

        message = json.dumps({"event": event_type, "data": data or {}})
        stale_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                stale_connections.append(connection)

        for stale in stale_connections:
            self.active_connections.discard(stale)


manager = ConnectionManager()


@router.websocket("/sync")
async def websocket_sync_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive with heartbeat ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
