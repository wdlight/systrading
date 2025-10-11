"""
Redis 캐싱 유틸리티
"""

import json
import redis
from typing import Optional, Any
from loguru import logger

from app.core.config import get_settings


class CacheService:
    """Redis 캐싱 서비스"""

    def __init__(self):
        settings = get_settings()

        try:
            # settings.REDIS_URL을 사용하여 연결
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis.ping()
            logger.info("✅ Redis 연결 성공")
        except Exception as e:
            logger.warning(f"⚠️ Redis 연결 실패: {e}")
            self.redis = None

    def get(self, key: str) -> Optional[Any]:
        """캐시 조회"""
        if not self.redis:
            return None

        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"캐시 조회 실패: {e}")

        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시 저장"""
        if not self.redis:
            return

        try:
            self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.error(f"캐시 저장 실패: {e}")

    def delete(self, key: str):
        """캐시 삭제"""
        if not self.redis:
            return

        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"캐시 삭제 실패: {e}")
