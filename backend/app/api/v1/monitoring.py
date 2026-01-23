# app/api/v1/monitoring.py
from flask import Blueprint, jsonify
from datetime import datetime
import os
import logging

from app.services.redis_service import RedisService
from app.services.api_metrics_service import api_metrics_service
from app.services.cache_warming_service import cache_warming_service

logger = logging.getLogger(__name__)
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/v1/monitoring')


@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    redis_service = RedisService.get_instance()
    
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "healthy",
            "redis": redis_service.get_connection_info(),
            "redis_connected": not redis_service._use_memory_cache
        }
    }
    
    return jsonify(health), 200


@monitoring_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get API metrics and usage statistics."""
    try:
        metrics = api_metrics_service.get_metrics()
        summary = api_metrics_service.get_summary()
        
        return jsonify({
            "success": True,
            "summary": summary,
            "services": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitoring_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics."""
    try:
        redis_service = RedisService.get_instance()
        
        stats = {
            "connection_type": redis_service.get_connection_info(),
            "using_memory_fallback": redis_service._use_memory_cache,
            "redis_type": redis_service._redis_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify({
            "success": True,
            "cache_stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching cache stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitoring_bp.route('/status', methods=['GET'])
def get_status():
    """Get comprehensive system status."""
    try:
        redis_service = RedisService.get_instance()
        summary = api_metrics_service.get_summary()
        warming_stats = cache_warming_service.get_stats()
        
        status = {
            "environment": os.getenv("FLASK_ENV", "production"),
            "uptime_seconds": summary.get("uptime_seconds", 0),
            "total_api_calls": summary.get("total_api_calls", 0),
            "cache_hit_rate": round(summary.get("overall_cache_hit_rate", 0), 2),
            "redis_status": "connected" if not redis_service._use_memory_cache else "fallback",
            "pending_requests": summary.get("pending_requests", 0),
            "services_tracked": summary.get("services", []),
            "alpha_vantage_configured": bool(os.getenv("ALPHA_VANTAGE_API_KEY")),
            "cache_warming": warming_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify({
            "success": True,
            "status": status
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitoring_bp.route('/warm-cache', methods=['POST'])
def trigger_cache_warming():
    """Manually trigger cache warming for popular symbols."""
    try:
        cache_warming_service.start_background_warming()
        return jsonify({
            "success": True,
            "message": "Cache warming triggered",
            "stats": cache_warming_service.get_stats()
        }), 200
    except Exception as e:
        logger.error(f"Error triggering cache warming: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
