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
    """Wrapper for Upstash Redis to provide consistent interface"""
    
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


class RedisService:
    """Centralized Redis service for caching with Upstash and in-memory fallback"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RedisService()
        return cls._instance
    
    def __init__(self):
        self.client = None
        self._memory_cache = InMemoryCache()
        self._use_memory_cache = True
        self._redis_type = None
        
        # Try Upstash Redis first (recommended for Replit)
        upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
        upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
        
        if upstash_url and upstash_token:
            self.client = self._init_upstash(upstash_url, upstash_token)
            if self.client:
                self._use_memory_cache = False
                self._redis_type = 'upstash'
                print("Upstash Redis connection established")
        
        # Fall back to local Redis if Upstash not configured
        if self.client is None:
            self.client = self._init_local_redis()
            if self.client:
                self._use_memory_cache = False
                self._redis_type = 'local'
        
        if self._use_memory_cache:
            print("Using in-memory cache fallback (Redis unavailable)")
    
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
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or in-memory fallback)"""
        if self._use_memory_cache:
            return self._memory_cache.get(key)
        
        if not self.client:
            return self._memory_cache.get(key)
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Redis get error for key {key}: {e}")
            return self._memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Set value in cache with TTL (Redis or in-memory fallback)"""
        if self._use_memory_cache:
            return self._memory_cache.set(key, value, ttl)
        
        if not self.client:
            return self._memory_cache.set(key, value, ttl)
        try:
            serialized = json.dumps(value, default=self._json_serializer)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Redis set error for key {key}: {e}")
            return self._memory_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache (Redis or in-memory fallback)"""
        if self._use_memory_cache:
            return self._memory_cache.delete(key)
        
        if not self.client:
            return self._memory_cache.delete(key)
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Redis delete error for key {key}: {e}")
            return self._memory_cache.delete(key)
    
    def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern (Redis or in-memory fallback)"""
        if self._use_memory_cache:
            return self._memory_cache.delete_pattern(pattern)
        
        if not self.client:
            return self._memory_cache.delete_pattern(pattern)
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
            return self._memory_cache.delete_pattern(pattern)
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in Redis"""
        if self._use_memory_cache or not self.client:
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
        if self._use_memory_cache:
            return "In-memory cache (no Redis configured)"
        elif self._redis_type == 'upstash':
            return "Upstash Redis (cloud)"
        elif self._redis_type == 'local':
            return "Local Redis"
        return "Unknown"
