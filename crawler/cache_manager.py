import redis
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CacheManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True
                )
                self.cache_ttl = 24 * 60 * 60  # 24 hours
                self.initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {str(e)}")
                self.redis_client = None

    def get_key(self, address: str, network: str) -> str:
        """Generate cache key for address and network combination"""
        return f"misttrack:{network.lower()}:{address.lower()}"

    def get_cached_result(self, address: str, network: str) -> Optional[Dict[str, Any]]:
        """Get cached result for an address"""
        if not self.redis_client:
            return None

        try:
            key = self.get_key(address, network)
            cached_data = self.redis_client.get(key)
            if cached_data:
                logger.info(f"Cache hit for {address} on {network}")
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached result: {str(e)}")
        return None

    def cache_result(self, address: str, network: str, result: Dict[str, Any]):
        """Cache result for an address"""
        if not self.redis_client:
            return

        try:
            key = self.get_key(address, network)
            self.redis_client.setex(
                key,
                self.cache_ttl,
                json.dumps(result)
            )
            logger.info(f"Cached result for {address} on {network}")
        except Exception as e:
            logger.error(f"Error caching result: {str(e)}")

    def clear_cache(self, address: str = None, network: str = None):
        """Clear cache for specific address or all addresses"""
        if not self.redis_client:
            return

        try:
            if address and network:
                key = self.get_key(address, network)
                self.redis_client.delete(key)
                logger.info(f"Cleared cache for {address} on {network}")
            else:
                pattern = "misttrack:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info("Cleared all cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
