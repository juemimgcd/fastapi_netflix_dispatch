import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from conf.settings import settings

logger = logging.getLogger(__name__)

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,  # 注意：这里是 decode_responses
)


async def get_cache_json(key: str) -> Any | None:
    try:
        raw = await redis_client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw
    except Exception:
        logger.exception("Redis cache_get_json failed for key=%s", key)
        return None


async def set_cache(key: str, value: Any, expire: int = 5) -> bool:

    try:
        raw = json.dumps(value, ensure_ascii=False, default=str)
        await redis_client.set(key, raw, ex=expire)
        return True
    except Exception:
        logger.exception("Redis set_cache_json failed for key=%s", key)
        return False


def make_cache_key(prefix: str, parts: dict[str, Any]) -> str:
    seg: list[str] = [prefix]
    for k in sorted(parts.keys()):
        v = parts[k]
        if v is None:
            v_str = "null"
        elif isinstance(v, bool):
            v_str = "1" if v else "0"
        else:
            v_str = str(v)
        seg.append(f"{k}={v_str}")
    return "|".join(seg)
