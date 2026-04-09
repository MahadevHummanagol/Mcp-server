# C:\mcp-server-demo\connection.py

from redis import Redis
from redis.exceptions import RedisError
from datetime import datetime
import json

from config import REDIS_CONFIG

# Initialize Redis client (this should NOT be part of any Pydantic model)
redis_client = Redis(**REDIS_CONFIG)

def get_connection_status() -> dict:
    """Check Redis connection status"""
    try:
        redis_client.ping()
        return {
            "status": "connected",
            "timestamp": datetime.now().isoformat(),
            "config": REDIS_CONFIG
        }
    except RedisError as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
