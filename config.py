# C:\mcp-server-demo\config.py

from typing import TypedDict
from dotenv import load_dotenv
import os

class RedisConfig(TypedDict):
    host: str
    port: int
    db: int
    decode_responses: bool

# Load environment variables from .env file
load_dotenv()

# Default Redis configuration
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST"),
    "port": int(os.getenv("REDIS_PORT")),
    "db": int(os.getenv("REDIS_DB", 0)),
    "password": os.getenv("REDIS_PASSWORD"),
    "decode_responses": True  # Automatically decode response bytes to strings
}
