# app/services/redis_service.py
import redis
import json
import os
from datetime import datetime
from typing import Any, Optional, Dict, List
import hashlib

class RedisService:
    """Centralized Redis service for caching"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RedisService()
        return cls._instance
    
    def __init__(self):
        self.client = self._init_redis()
    
    def _init_redis(self):
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
            print("Redis connection established")
            return client
        except Exception as e:
            print(f"Redis connection failed: {e}")
            return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.client:
            return None
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Set value in Redis cache with TTL"""
        if not self.client:
            return False
        try:
            serialized = json.dumps(value, default=self._json_serializer)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Redis set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.client:
            return False
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Redis delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern"""
        if not self.client:
            return False
        try:
            keys = []
            cursor = '0'
            while cursor != 0:
                cursor, found_keys = self.client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                keys.extend(found_keys)
            
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis delete pattern error: {e}")
            return False
    
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
        if not self.client:
            return
        pattern = f"user:{uid}:*"
        self.delete_pattern(pattern)