from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
import structlog

from src.core.config import settings
from src.api.websockets.manager import manager

logger = structlog.get_logger(__name__)

router = APIRouter()


async def get_user_from_token(token: str) -> dict | None:
    """Decode JWT token and extract user info."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret,
            algorithms=[settings.jwt.algorithm],
            audience=settings.jwt.audience,
        )
        return {
            "user_id": int(payload.get("sub")),
            "tenant_id": int(payload.get("tenant")),
        }
    except JWTError as e:
        logger.error("websocket_auth_failed", error=str(e))
        return None


@router.websocket("/ws/tickets/{ticket_id}")
async def websocket_ticket(
    websocket: WebSocket,
    ticket_id: int,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time ticket updates.

    Client connects with:
    - ws://localhost:8000/v1/ws/tickets/123?token=<jwt_token>

    Receives updates when:
    - New messages are added
    - Ticket status changes
    - AI responses are generated
    """
    user_info = await get_user_from_token(token)
    if not user_info:
        await websocket.close(code=4001, reason="Invalid authentication")
        return

    await manager.connect(websocket, ticket_id=ticket_id, user_id=user_info["user_id"])

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "ticket_id": ticket_id,
            "user_id": user_info["user_id"],
        })

        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_json()

            # Handle ping/pong
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, ticket_id=ticket_id, user_id=user_info["user_id"])
        logger.info("websocket_client_disconnected", ticket_id=ticket_id)


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for AI chat streaming.

    Client sends:
    - {"type": "ask", "content": "What is...?"}

    Server streams:
    - {"type": "stream", "chunk": "partial response..."}
    - {"type": "complete", "full_content": "..."}
    """
    user_info = await get_user_from_token(token)
    if not user_info:
        await websocket.close(code=4001, reason="Invalid authentication")
        return

    await manager.connect(websocket, user_id=user_info["user_id"])

    try:
        await websocket.send_json({"type": "connected"})

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if data.get("type") == "ask":
                # Stream AI response
                from src.services.agent import AgentService
                from src.core.db import get_session_context

                async with get_session_context() as session:
                    agent = AgentService(session)

                    # Send start marker
                    await websocket.send_json({"type": "stream_start"})

                    response = await agent.answer_question(
                        tenant_id=user_info["tenant_id"],
                        question=data.get("content", ""),
                    )

                    await websocket.send_json({
                        "type": "complete",
                        "content": response.content,
                        "kb_hits": len(response.kb_hits),
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id=user_info["user_id"])
        logger.info("websocket_chat_disconnected", user_id=user_info["user_id"])
