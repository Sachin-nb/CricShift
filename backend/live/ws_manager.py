"""
WebSocket Live Connection Manager
Handles client connections and live match streaming updates.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("backend.ws")


class LiveWebSocketManager:
    """Manages active WebSocket connections grouped by match_id."""

    def __init__(self):
        self._active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, match_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if match_id not in self._active_connections:
                self._active_connections[match_id] = set()
            self._active_connections[match_id].add(websocket)
        logger.info(f"WebSocket client connected to match '{match_id}'. Total: {len(self._active_connections[match_id])}")

    async def disconnect(self, match_id: str, websocket: WebSocket):
        async with self._lock:
            if match_id in self._active_connections:
                self._active_connections[match_id].discard(websocket)
                if not self._active_connections[match_id]:
                    del self._active_connections[match_id]
        logger.info(f"WebSocket client disconnected from match '{match_id}'.")

    async def broadcast(self, match_id: str, message: Dict[str, Any]):
        """Broadcasts a JSON message to all active clients for a match."""
        async with self._lock:
            connections = list(self._active_connections.get(match_id, []))

        dead_connections = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message to client on match '{match_id}': {e}")
                dead_connections.append(ws)

        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    if match_id in self._active_connections:
                        self._active_connections[match_id].discard(ws)


ws_manager = LiveWebSocketManager()
