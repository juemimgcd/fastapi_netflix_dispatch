from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt
from sqlalchemy import select

from conf.db_conf import AsyncSessionLocal
from conf.settings import settings
from models.users import User
from utils.ws_pubsub import get_pubsub_for_user, redis_client

router = APIRouter()

logger = logging.getLogger(__name__)


async def _authenticate_token_get_user_id(token: str) -> Optional[uuid.UUID]:
    """
    Decode JWT token and return user_id (UUID) or None on failure.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        sub = payload.get("sub")
        if not sub:
            return None
        return uuid.UUID(sub)
    except Exception:
        return None


@router.websocket("/ws/notifications")
async def websocket_notifications(ws: WebSocket):
    """
    WebSocket endpoint to stream notifications to authenticated user.

    Expected URL: /api/v1/ws/notifications?token=<JWT>
    """
    # 1) token from query params
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=1008)
        return

    # 2) decode token -> user id
    user_id = await _authenticate_token_get_user_id(token)
    if user_id is None:
        await ws.close(code=1008)
        return

    # 3) verify user exists
    async with AsyncSessionLocal() as db:
        try:
            resp = await db.execute(select(User).where(User.id == user_id))
            user = resp.scalar_one_or_none()
        except Exception:
            user = None

    if user is None:
        await ws.close(code=1008)
        return

    # 4) accept the websocket
    await ws.accept()
    channel = f"notifications:user:{user.id}"

    # 5) subscribe to redis pubsub
    pubsub = await get_pubsub_for_user(user.id)

    # 6) loop: poll pubsub for messages and forward to websocket
    try:
        while True:
            # non-blocking check for pubsub messages (timeout)
            try:
                # pubsub.get_message is a coroutine; timeout-based polling
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error while reading from redis pubsub for channel %s", channel)
                msg = None

            if msg and msg.get("type") == "message":
                data = msg.get("data")
                # data should be a JSON string (published by publish_notification)
                if isinstance(data, (bytes, bytearray)):
                    try:
                        data = data.decode("utf-8")
                    except Exception:
                        data = data.decode(errors="ignore")
                # forward to client
                try:
                    await ws.send_text(str(data))
                except WebSocketDisconnect:
                    raise

            # Also check if client sent a close / ping (receive_text with small timeout)
            # We use small wait_for to detect client disconnects gracefully.
            try:
                # try to receive json/text with small timeout to detect client side messages
                # If there's no incoming client message, wait_for will timeout and we continue polling Redis.
                await asyncio.wait_for(ws.receive_text(), timeout=0.1)
                # We ignore incoming client messages; they can be used for ping/pong keepalive if you want.
            except asyncio.TimeoutError:
                # no client message; continue pubsub polling
                pass
            except WebSocketDisconnect:
                raise
            except Exception:
                # ignore other receive errors, continue
                pass

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user %s", user.id)
    finally:
        try:
            # Unsubscribe and close pubsub
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception:
            logger.exception("Error closing pubsub for channel %s", channel)
        try:
            await ws.close()
        except Exception:
            pass