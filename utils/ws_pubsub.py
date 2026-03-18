"""
Redis Pub/Sub helpers for notifications.

职责：
- 提供 publish_notification(user_id, payload) 给业务方在 commit 之后调用。
- 提供低层 pubsub client access（用于 websocket handler 订阅）。

实现依赖 redis.asyncio (redis-py >=5)。
"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from conf.settings import settings

logger = logging.getLogger(__name__)

# 全局 redis client（复用，不要在每次 publish/subscribe 都新建连接）
redis_client: "redis.Redis" = redis.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)


async def publish_notification(user_id: str | bytes | Any, payload: dict[str, Any]) -> None:
    """
    Publish a notification payload to the user's redis channel.

    - user_id: uuid.UUID or its str representation (we treat it as str for channel key)
    - payload: a JSON-serializable dict (message/ref_type/ref_id/created_at 等)
    """
    channel = f"notifications:user:{user_id}"
    try:
        raw = json.dumps(payload, default=str, ensure_ascii=False)
        await redis_client.publish(channel, raw)
    except Exception:
        logger.exception("Failed to publish notification to channel %s", channel)


async def get_pubsub_for_user(user_id: str | Any) -> "redis.client.PubSub":
    """
    Return a PubSub object already subscribed to the user's channel.
    Caller is responsible to close/unsubscribe it.
    """
    channel = f"notifications:user:{user_id}"
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    return pubsub