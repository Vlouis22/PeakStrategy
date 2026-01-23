import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class APICallMetrics:
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time_ms: float = 0.0
    last_call_time: Optional[str] = None
    rate_limit_hits: int = 0


@dataclass
class RequestDeduplicationEntry:
    result: Any = None
    error: Optional[str] = None
    completed: bool = False
    waiters: List[threading.Event] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class APIMetricsService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_service()
        return cls._instance
    
    def _init_service(self):
        self._metrics: Dict[str, APICallMetrics] = defaultdict(APICallMetrics)
        self._response_times: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._pending_requests: Dict[str, RequestDeduplicationEntry] = {}
        self._pending_lock = threading.Lock()
        self._request_timeout = 60  # seconds
        self._max_response_times = 100  # keep last N response times
        self._started_at = datetime.utcnow()
        logger.info("APIMetricsService initialized")
    
    def record_api_call(
        self,
        service_name: str,
        success: bool,
        response_time_ms: float,
        cached: bool = False,
        rate_limited: bool = False
    ):
        with self._lock:
            metrics = self._metrics[service_name]
            metrics.total_calls += 1
            
            if success:
                metrics.successful_calls += 1
            else:
                metrics.failed_calls += 1
            
            if cached:
                metrics.cache_hits += 1
            else:
                metrics.cache_misses += 1
            
            if rate_limited:
                metrics.rate_limit_hits += 1
            
            metrics.last_call_time = datetime.utcnow().isoformat()
            
            response_times = self._response_times[service_name]
            response_times.append(response_time_ms)
            if len(response_times) > self._max_response_times:
                response_times.pop(0)
            
            metrics.avg_response_time_ms = sum(response_times) / len(response_times)
    
    def get_metrics(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            if service_name:
                metrics = self._metrics.get(service_name, APICallMetrics())
                return {
                    service_name: {
                        "total_calls": metrics.total_calls,
                        "successful_calls": metrics.successful_calls,
                        "failed_calls": metrics.failed_calls,
                        "success_rate": (
                            metrics.successful_calls / metrics.total_calls * 100
                            if metrics.total_calls > 0 else 0
                        ),
                        "cache_hits": metrics.cache_hits,
                        "cache_misses": metrics.cache_misses,
                        "cache_hit_rate": (
                            metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100
                            if (metrics.cache_hits + metrics.cache_misses) > 0 else 0
                        ),
                        "avg_response_time_ms": round(metrics.avg_response_time_ms, 2),
                        "rate_limit_hits": metrics.rate_limit_hits,
                        "last_call_time": metrics.last_call_time
                    }
                }
            
            all_metrics = {}
            for name, metrics in self._metrics.items():
                all_metrics[name] = {
                    "total_calls": metrics.total_calls,
                    "successful_calls": metrics.successful_calls,
                    "failed_calls": metrics.failed_calls,
                    "success_rate": (
                        metrics.successful_calls / metrics.total_calls * 100
                        if metrics.total_calls > 0 else 0
                    ),
                    "cache_hits": metrics.cache_hits,
                    "cache_misses": metrics.cache_misses,
                    "cache_hit_rate": (
                        metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100
                        if (metrics.cache_hits + metrics.cache_misses) > 0 else 0
                    ),
                    "avg_response_time_ms": round(metrics.avg_response_time_ms, 2),
                    "rate_limit_hits": metrics.rate_limit_hits,
                    "last_call_time": metrics.last_call_time
                }
            return all_metrics
    
    def get_summary(self) -> Dict[str, Any]:
        metrics = self.get_metrics()
        total_calls = sum(m["total_calls"] for m in metrics.values())
        total_cache_hits = sum(m["cache_hits"] for m in metrics.values())
        total_cache_misses = sum(m["cache_misses"] for m in metrics.values())
        
        return {
            "uptime_seconds": (datetime.utcnow() - self._started_at).total_seconds(),
            "total_api_calls": total_calls,
            "total_cache_hits": total_cache_hits,
            "total_cache_misses": total_cache_misses,
            "overall_cache_hit_rate": (
                total_cache_hits / (total_cache_hits + total_cache_misses) * 100
                if (total_cache_hits + total_cache_misses) > 0 else 0
            ),
            "services": list(metrics.keys()),
            "pending_requests": len(self._pending_requests)
        }
    
    def acquire_request_lock(self, request_key: str) -> tuple[bool, Optional[Any]]:
        with self._pending_lock:
            self._cleanup_stale_requests()
            
            if request_key in self._pending_requests:
                entry = self._pending_requests[request_key]
                if entry.completed:
                    return False, entry.result
                
                wait_event = threading.Event()
                entry.waiters.append(wait_event)
                return False, wait_event
            
            self._pending_requests[request_key] = RequestDeduplicationEntry()
            return True, None
    
    def complete_request(self, request_key: str, result: Any, error: Optional[str] = None):
        with self._pending_lock:
            if request_key in self._pending_requests:
                entry = self._pending_requests[request_key]
                entry.result = result
                entry.error = error
                entry.completed = True
                
                for waiter in entry.waiters:
                    waiter.set()
                
                del self._pending_requests[request_key]
    
    def wait_for_request(self, wait_event: threading.Event, timeout: float = 30.0) -> Optional[Any]:
        wait_event.wait(timeout=timeout)
        return None
    
    def _cleanup_stale_requests(self):
        now = time.time()
        stale_keys = [
            key for key, entry in self._pending_requests.items()
            if now - entry.created_at > self._request_timeout
        ]
        for key in stale_keys:
            entry = self._pending_requests[key]
            for waiter in entry.waiters:
                waiter.set()
            del self._pending_requests[key]


api_metrics_service = APIMetricsService()
