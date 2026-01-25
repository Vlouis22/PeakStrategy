# app/services/redis_service.py
import redis
import json
import os
from datetime import datetime
from typing import Any, Optional, Dict, List
import hashlib
import threading
import time

class InMemoryCache:
    """Simple in-memory cache with TTL support as fallback when Redis is unavailable"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item['expires_at'] > time.time():
                    return item['value']
                else:
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
            return True
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def delete_pattern(self, pattern: str) -> bool:
        import fnmatch
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
            for k in keys_to_delete:
                del self._cache[k]
            return True
    
    def cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            now = time.time()
            expired = [k for k, v in self._cache.items() if v['expires_at'] <= now]
            for k in expired:
                del self._cache[k]


class UpstashRedisWrapper:
    """Wrapper for Upstash Redis to provide consistent interface with batch support"""
    
    def __init__(self, upstash_client):
        self._client = upstash_client
    
    def get(self, key: str) -> Optional[str]:
        return self._client.get(key)
    
    def setex(self, key: str, ttl: int, value: str) -> bool:
        self._client.set(key, value, ex=ttl)
        return True
    
    def delete(self, key: str) -> int:
        return self._client.delete(key)
    
    def scan(self, cursor: int = 0, match: str = "*", count: int = 100):
        result = self._client.scan(cursor=cursor, match=match, count=count)
        return result
    
    def incrby(self, key: str, amount: int = 1) -> int:
        return self._client.incrby(key, amount)
    
    def ping(self) -> bool:
        return self._client.ping() == "PONG"
    
    def mget(self, *keys: str) -> List[Optional[str]]:
        """Get multiple keys in a single request (true batch operation)."""
        if not keys:
            return []
        return self._client.mget(*keys)
    
    def pipeline_setex(self, items: Dict[str, tuple]) -> bool:
        """Set multiple key-value pairs with TTL using pipeline.
        items: Dict[key, (ttl, value)]
        """
        if not items:
            return True
        pipeline = self._client.pipeline()
        for key, (ttl, value) in items.items():
            pipeline.set(key, value, ex=ttl)
        pipeline.exec()
        return True


class RedisService:
    """Centralized Redis service for caching with two-tier architecture:
    - L1: Fast local in-memory cache (60s TTL) for hot data
    - L2: Upstash Redis (cloud) for shared persistent cache
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RedisService()
        return cls._instance
    
    def __init__(self):
        self.client = None
        self._l1_cache = InMemoryCache()  # L1: Local fast cache (always enabled)
        self._l1_ttl = 60  # L1 cache TTL in seconds (1 minute)
        self._redis_only = False  # When True, skip L1 cache
        self._redis_type = None
        
        # Try Upstash Redis first (recommended for Replit)
        upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
        upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
        print(f"\n\nUpstash URL: {upstash_url}, Token: {'set' if upstash_token else 'not set'}")
        
        if upstash_url and upstash_token:
            self.client = self._init_upstash(upstash_url, upstash_token)
            if self.client:
                self._redis_type = 'upstash'
                print("Upstash Redis connection established")
        
        # Fall back to local Redis if Upstash not configured
        if self.client is None:
            self.client = self._init_local_redis()
            if self.client:
                self._redis_type = 'local'
        
        if self.client is None:
            print("Using in-memory cache only (Redis unavailable)")
    
    def _init_upstash(self, url: str, token: str):
        """Initialize Upstash Redis connection"""
        try:
            from upstash_redis import Redis as UpstashRedis
            client = UpstashRedis(url=url, token=token)
            # Test connection
            client.ping()
            return UpstashRedisWrapper(client)
        except Exception as e:
            print(f"Upstash Redis connection failed: {e}")
            return None
    
    def _init_local_redis(self):
        """Initialize local Redis connection"""
        try:
            host = os.getenv('REDIS_HOST', 'localhost')
            port = int(os.getenv('REDIS_PORT', 6379))
            db = int(os.getenv('REDIS_DB', 0))
            password = os.getenv('REDIS_PASSWORD', None)
            
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=20
            )
            client.ping()
            print("Local Redis connection established")
            return client
        except Exception as e:
            print(f"Local Redis connection failed: {e}")
            return None
    
    def get(self, key: str, skip_l1: bool = False) -> Optional[Any]:
        """Get value from two-tier cache (L1 local -> L2 Redis)"""
        # Check L1 cache first (fastest)
        if not skip_l1:
            l1_value = self._l1_cache.get(key)
            if l1_value is not None:
                return l1_value
        
        # Fall back to L2 (Redis)
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                parsed = json.loads(value)
                # Populate L1 cache for next request
                if not skip_l1:
                    self._l1_cache.set(key, parsed, self._l1_ttl)
                return parsed
            return None
        except Exception as e:
            print(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 60, skip_l1: bool = False) -> bool:
        """Set value in two-tier cache (L1 local + L2 Redis)"""
        # Always set in L1 cache for fast local access
        if not skip_l1:
            l1_ttl = min(ttl, self._l1_ttl)  # L1 TTL is capped at 60s
            self._l1_cache.set(key, value, l1_ttl)
        
        # Set in L2 (Redis) if available
        if not self.client:
            return True  # L1 succeeded
        
        try:
            serialized = json.dumps(value, default=self._json_serializer)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Redis set error for key {key}: {e}")
            return True  # L1 still succeeded
    
    def delete(self, key: str) -> bool:
        """Delete key from both cache tiers"""
        # Delete from L1
        self._l1_cache.delete(key)
        
        # Delete from L2 (Redis)
        if not self.client:
            return True
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error for key {key}: {e}")
            return True
    
    def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern from both cache tiers"""
        # Delete from L1
        self._l1_cache.delete_pattern(pattern)
        
        # Delete from L2 (Redis)
        if not self.client:
            return True
        try:
            keys = []
            cursor = 0
            while True:
                result = self.client.scan(cursor=cursor, match=pattern, count=100)
                if isinstance(result, tuple):
                    cursor, found_keys = result
                else:
                    break
                keys.extend(found_keys)
                if cursor == 0:
                    break
            
            if keys:
                for key in keys:
                    self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete pattern error: {e}")
            return True
    
    def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get multiple keys efficiently - checks L1 first, then uses MGET for L2"""
        results = {}
        keys_to_fetch_from_redis = []
        key_index_map = {}  # Map key to index for matching MGET results
        
        # Check L1 cache first for all keys
        for key in keys:
            l1_value = self._l1_cache.get(key)
            if l1_value is not None:
                results[key] = l1_value
            else:
                key_index_map[key] = len(keys_to_fetch_from_redis)
                keys_to_fetch_from_redis.append(key)
        
        # Fetch remaining from Redis using MGET (single request for all keys)
        if keys_to_fetch_from_redis and self.client:
            try:
                # Use MGET for true batch operation - single network round-trip
                values = self.client.mget(*keys_to_fetch_from_redis)
                
                for i, key in enumerate(keys_to_fetch_from_redis):
                    value = values[i] if i < len(values) else None
                    if value:
                        try:
                            parsed = json.loads(value)
                            results[key] = parsed
                            # Populate L1 cache
                            self._l1_cache.set(key, parsed, self._l1_ttl)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                print(f"Redis get_multi MGET error: {e}")
        
        return results
    
    def set_multi(self, items: Dict[str, Any], ttl: int = 60) -> bool:
        """Batch set multiple key-value pairs using pipeline (single network round-trip)"""
        # Set all in L1 cache
        l1_ttl = min(ttl, self._l1_ttl)
        for key, value in items.items():
            self._l1_cache.set(key, value, l1_ttl)
        
        # Set all in L2 (Redis) using pipeline
        if not self.client:
            return True
        
        try:
            # Prepare pipeline items: Dict[key, (ttl, serialized_value)]
            pipeline_items = {}
            for key, value in items.items():
                serialized = json.dumps(value, default=self._json_serializer)
                pipeline_items[key] = (ttl, serialized)
            
            # Use pipeline for true batch operation - single network round-trip
            self.client.pipeline_setex(pipeline_items)
            return True
        except Exception as e:
            print(f"Redis set_multi pipeline error: {e}")
            return True  # L1 still succeeded
    
    def get_with_stale(self, key: str, max_stale_seconds: int = 300) -> tuple:
        """Get value with stale-while-revalidate support.
        Returns (value, is_stale) tuple.
        If cache is expired but within max_stale_seconds, returns stale data with is_stale=True.
        """
        # Check L1 first
        l1_value = self._l1_cache.get(key)
        if l1_value is not None:
            return (l1_value, False)
        
        # Check Redis with stale support
        if not self.client:
            return (None, False)
        
        try:
            value = self.client.get(key)
            if value:
                parsed = json.loads(value)
                # Check if data includes timestamp for staleness check
                if isinstance(parsed, dict) and 'timestamp' in parsed:
                    try:
                        from datetime import datetime
                        cached_time = datetime.fromisoformat(parsed['timestamp'])
                        age = (datetime.now() - cached_time).total_seconds()
                        # If within stale window, return it but mark as stale
                        if age < max_stale_seconds:
                            # Populate L1 cache with shorter TTL for stale data
                            self._l1_cache.set(key, parsed, 30)
                            return (parsed, age > self._l1_ttl)
                    except:
                        pass
                # Populate L1 cache
                self._l1_cache.set(key, parsed, self._l1_ttl)
                return (parsed, False)
            return (None, False)
        except Exception as e:
            print(f"Redis get_with_stale error for key {key}: {e}")
            return (None, False)
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in Redis"""
        if not self.client:
            return 0
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            print(f"Redis increment error: {e}")
            return 0
    
    def _json_serializer(self, obj):
        """JSON serializer for datetime objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def generate_hash(self, data: Any) -> str:
        """Generate MD5 hash of data"""
        data_str = json.dumps(data, sort_keys=True, default=self._json_serializer)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get_user_cache_key(self, uid: str, endpoint: str, *args) -> str:
        """Generate cache key for user-specific data"""
        parts = [f"user:{uid}", f"endpoint:{endpoint}"]
        if args:
            parts.extend([str(arg) for arg in args])
        return ":".join(parts)
    
    def invalidate_user_cache(self, uid: str):
        """Invalidate all cache for a specific user"""
        pattern = f"user:{uid}:*"
        self.delete_pattern(pattern)
    
    def get_connection_info(self) -> str:
        """Get information about the current Redis connection"""
        if self.client is None:
            return "In-memory cache only (no Redis configured)"
        elif self._redis_type == 'upstash':
            return "Upstash Redis (cloud) + L1 local cache"
        elif self._redis_type == 'local':
            return "Local Redis + L1 local cache"
        return "Unknown"
    
    def get_l1_stats(self) -> Dict[str, Any]:
        """Get L1 cache statistics"""
        with self._l1_cache._lock:
            total_keys = len(self._l1_cache._cache)
            now = time.time()
            valid_keys = sum(1 for v in self._l1_cache._cache.values() if v['expires_at'] > now)
            return {
                "total_keys": total_keys,
                "valid_keys": valid_keys,
                "expired_keys": total_keys - valid_keys
            }
