"""简单内存缓存，按会话/文件维度缓存5分钟内的计算结果"""
import time
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimpleCache:
    """简单内存缓存实现"""
    
    def __init__(self, default_ttl: int = 300):
        """
        初始化缓存
        
        Args:
            default_ttl: 默认过期时间（秒），默认5分钟
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        if key not in self._cache:
            return None
        
        value, expire_time = self._cache[key]
        
        if time.time() > expire_time:
            # 已过期，删除
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认值
        """
        if ttl is None:
            ttl = self.default_ttl
        
        expire_time = time.time() + ttl
        self._cache[key] = (value, expire_time)
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
    
    def delete(self, key: str):
        """删除指定缓存"""
        if key in self._cache:
            del self._cache[key]
    
    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expire_time) in self._cache.items()
            if current_time > expire_time
        ]
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


# 全局缓存实例
_metrics_cache = SimpleCache(default_ttl=300)


def get_cache() -> SimpleCache:
    """获取全局缓存实例"""
    return _metrics_cache

