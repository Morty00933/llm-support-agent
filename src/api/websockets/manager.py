from __future__ import annotations

from typing import Dict, Set
from fastapi import WebSocket
import structlog

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # Map: ticket_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

        # Map: user_id -> set of WebSocket connections
        self.user_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        ticket_id: int | None = None,
        user_id: int | None = None,
    ):
        """Accept WebSocket connection and register it."""
        await websocket.accept()

        if ticket_id:
            if ticket_id not in self.active_connections:
                self.active_connections[ticket_id] = set()
            self.active_connections[ticket_id].add(websocket)
            logger.info("websocket_connected_to_ticket", ticket_id=ticket_id)

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
            logger.info("websocket_connected_for_user", user_id=user_id)

    def disconnect(
        self,
        websocket: WebSocket,
        ticket_id: int | None = None,
        user_id: int | None = None,
    ):
        """Remove WebSocket connection."""
        if ticket_id and ticket_id in self.active_connections:
            self.active_connections[ticket_id].discard(websocket)
            if not self.active_connections[ticket_id]:
                del self.active_connections[ticket_id]
            logger.info("websocket_disconnected_from_ticket", ticket_id=ticket_id)

        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
            logger.info("websocket_disconnected_for_user", user_id=user_id)

    async def send_to_ticket(self, ticket_id: int, message: dict):
        """Broadcast message to all connections watching a ticket."""
        if ticket_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[ticket_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_send_failed", ticket_id=ticket_id, error=str(e))
                disconnected.add(connection)

        # Clean up disconnected sockets
        for conn in disconnected:
            self.active_connections[ticket_id].discard(conn)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to all user's connections."""
        if user_id not in self.user_connections:
            return

        disconnected = set()
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_send_failed", user_id=user_id, error=str(e))
                disconnected.add(connection)

        # Clean up
        for conn in disconnected:
            self.user_connections[user_id].discard(conn)


# Global connection manager instance
manager = ConnectionManager()
