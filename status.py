#C:\mcp-server-demo\resources\status.py
# C:\mcp-server-demo\resources\status.py

import json
from connection import get_connection_status, redis_client

def connection_status() -> str:
    """Get current Redis connection status"""
    return json.dumps(get_connection_status(), indent=2)

def redis_info() -> str:
    """Get Redis server information"""
    try:
        info = redis_client.info()
        return json.dumps(info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
