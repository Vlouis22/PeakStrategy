import logging
import sys
import time
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional
from flask import request, g
import threading

_request_context = threading.local()


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(_request_context, 'request_id', 'no-request')
        record.user_id = getattr(_request_context, 'user_id', 'anonymous')
        return True


def setup_logging(app_name: str = "peakstrategy", level: str = "INFO"):
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s [%(request_id)s] [%(user_id)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    
    root_logger.addHandler(handler)
    
    for logger_name in ['werkzeug', 'urllib3', 'yfinance']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    return root_logger


def set_request_context(request_id: str, user_id: str = "anonymous"):
    _request_context.request_id = request_id
    _request_context.user_id = user_id


def clear_request_context():
    _request_context.request_id = 'no-request'
    _request_context.user_id = 'anonymous'


def get_request_id() -> str:
    return getattr(_request_context, 'request_id', 'no-request')


class PerformanceLogger:
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        self.checkpoints = []
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self.start_time) * 1000
        if exc_type is not None:
            self.logger.error(
                f"Failed: {self.operation_name} after {elapsed_ms:.2f}ms - {exc_val}"
            )
        else:
            level = logging.WARNING if elapsed_ms > 1000 else logging.DEBUG
            self.logger.log(
                level,
                f"Completed: {self.operation_name} in {elapsed_ms:.2f}ms"
            )
        return False
    
    def checkpoint(self, name: str):
        elapsed_ms = (time.time() - self.start_time) * 1000
        self.checkpoints.append((name, elapsed_ms))
        self.logger.debug(f"Checkpoint [{self.operation_name}]: {name} at {elapsed_ms:.2f}ms")


def log_performance(operation_name: Optional[str] = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            logger = logging.getLogger(func.__module__)
            
            with PerformanceLogger(op_name, logger):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_api_call(service_name: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"API Call [{service_name}]: {func.__name__} completed in {elapsed_ms:.2f}ms"
                )
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"API Call [{service_name}]: {func.__name__} failed after {elapsed_ms:.2f}ms - {e}"
                )
                raise
        return wrapper
    return decorator


def init_request_logging(app):
    @app.before_request
    def before_request():
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        g.request_id = request_id
        g.start_time = time.time()
        set_request_context(request_id)
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            elapsed_ms = (time.time() - g.start_time) * 1000
            response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
            response.headers['X-Response-Time'] = f"{elapsed_ms:.2f}ms"
        return response
    
    @app.teardown_request
    def teardown_request(exception=None):
        clear_request_context()
