# server.py – MCP Server with Redis & Azure Mistral integration

import sys
import os
import io
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Dict, List, Annotated

# UTF-8 output (Windows safe)
if os.name == "nt":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# MCP Core imports
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
from mcp import types

# Redis imports
from redis import Redis
from redis.exceptions import RedisError

# Pydantic for context
from pydantic import BaseModel, PrivateAttr

# Redis connection setup (your local module)
from connection import redis_client

# Additional resource imports
from resources.status import connection_status, redis_info
from resources.keys import list_keys

# -----------------------------------------------------------------------------------
# Tool imports (Avoid circular imports)
# from tools.basic import *
# from tools.lists import list_range as raw_list_range
# from tools.hashes import hash_set as raw_hash_set
# from tools.sets import set_add as raw_set_add
# from tools.pubsub import publish_message as raw_publish_message

# Azure Mistral
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential

# Azure Mistral Configuration
AZURE_ENDPOINT = "https://Mistral-Large-2411-clhld.--------------------"
AZURE_KEY = "5WCo1nlf7q----------------------"
AZURE_MODEL = "Mistral-Large-2411-clhld"

# Create client
mistral_client = ChatCompletionsClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY),
    api_version="2024-05-01-preview"
)

# -----------------------------------------------------------------------------------
class AppContext(Context, BaseModel):
    # Private Redis client attribute
    _redis: Redis = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._redis = redis_client

    @property
    def redis(self) -> Redis:
        return self._redis

    class Config:
        arbitrary_types_allowed = True

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    print("🚀 Redis connected")
    try:
        yield AppContext()
    finally:
        print("🔌 Redis context released")

# Initialize FastMCP with lifespan manager that yields AppContext
mcp = FastMCP("Demo MCP Server", lifespan=app_lifespan)


# -----------------------------------------------------------------------------------


# Tools

# @mcp.tool()
# def ask_mistral(question: str) -> str:
#     """Ask a question to the Azure Mistral LLM"""
#     messages = [
#         SystemMessage(content="You are a helpful assistant."),
#         UserMessage(content=question),
#     ]
#     response = mistral_client.complete(
#         messages=messages,
#         model=AZURE_MODEL,
#         max_tokens=1024,
#         temperature=0.3,
#     )
#     return response.choices[0].message.content.strip()

@mcp.tool()
def ask_mistral(question: str) -> str:
    """Ask a question to the Azure Mistral LLM with SME system prompt"""
    content = (
        "You are a subject matter expert, a data analyst and a business expert who has been running all types of "
        "retail chains and restaurant chains and are an advisor to a lot of these chains. "
        "You always provide your answers in a concise manner, by providing insights in the form of three sections - "
        "analysis, recommendations and anomalies. All these sections always have 3 bullet points of the most important "
        "insights put very concisely that are very easy to understand for the business owner. "
        "You never give vague responses and make your responses very specific and accurate according to the data "
        "in the project files. Do not provide any insights related to technology, as I don't have control over those calculations."
    )

    messages = [
        SystemMessage(content=content),
        UserMessage(content=question),
    ]
    response = mistral_client.complete(
        messages=messages,
        model=AZURE_MODEL,
        max_tokens=1024,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


@mcp.tool()
def list_range(key: str, start: int = 0, end: int = -1) -> str:
    return raw_list_range(key, start, end)


@mcp.tool()
def hash_set(key: str, field_values: Dict[str, str]) -> str:
    return raw_hash_set(key, field_values)


@mcp.tool()
def set_add(key: str, members: List[str]) -> str:
    return raw_set_add(key, members)


@mcp.tool()
def publish_message(channel: str, message: str) -> str:
    return raw_publish_message(channel, message)


# -----------------------------------------------------------------------------------
# Resources

@mcp.resource("redis://status")
def _connection_status() -> str:
    return connection_status()


@mcp.resource("redis://info")
def _redis_info() -> str:
    return redis_info()

#-----------------------------------------------------------------------

import re

# @mcp.tool()
# def auto_route(question: str) -> str:
#     q_lower = question.lower()

#     # Detect Redis status related queries
#     if "redis status" in q_lower or "is redis connected" in q_lower or "redis connection" in q_lower:
#         # Call Redis status resource directly (bypass LLM)
#         return _connection_status()

#     # Detect keys pattern queries like 'keys matching user-*' or 'list keys user-*'
#     match = re.search(r'keys?\s*(matching|for|with)?\s*([a-z0-9\-\*\?]+)', q_lower)
#     if match:
#         pattern = match.group(2)
#         # Call list_keys with extracted pattern
#         return list_keys(pattern)

#     # Fallback to LLM for other questions
#     return ask_mistral(question)
# server.py

from resources.keys import list_keys

@mcp.resource("redis://keys/{pattern}")
def list_keys_resource(pattern: str) -> str:
    return list_keys(pattern)

# @mcp.resource("redis://keys-with-data/{pattern}")
# def get_keys_with_data_resource(pattern: str) -> str:
#     return get_keys_with_data(pattern)


import re
import re
from resources.keys import list_keys

# @mcp.tool()
# def auto_route(question: str) -> str:
#     q_lower = question.lower()

#     # Redis connection status
#     if "redis status" in q_lower or "is redis connected" in q_lower or "redis connection" in q_lower:
#         return _connection_status()

#     # If user asks for key *data* or content
#     if "data" in q_lower or "report" in q_lower or "content" in q_lower:
#         match = re.search(r'key[s]?\s*(matching|for|with)?\s*([a-z0-9:\-\*\?]+)', question, re.IGNORECASE)
#         if match:
#             pattern = match.group(2)
#             return get_keys_with_data(pattern)

#     # If just asking for key names
#     match = re.search(r'keys?\s*(matching|for|with)?\s*([a-z0-9:\-\*\?]+)', question, re.IGNORECASE)
#     if match:
#         pattern = match.group(2)
#         return list_keys(pattern)

#     # Otherwise fallback to LLM
#     return ask_mistral(question)


# @mcp.tool()
# def auto_route(question: str) -> str:
#     q_lower = question.lower()

#     # Redis connection check
#     if "redis status" in q_lower or "is redis connected" in q_lower or "redis connection" in q_lower:
#         return _connection_status()

#     # Generate report from Redis data
#     if "generate report" in q_lower or "business report" in q_lower:
#         match = re.search(r'key[s]?\s*(matching|for|with)?\s*([a-z0-9:\-\*\?]+)', question, re.IGNORECASE)
#         if match:
#             pattern = match.group(2)
#             data_json = get_keys_with_data(pattern)
#             # Send this data to LLM for analysis
#             return ask_mistral(f"""You are a business analyst.
# Generate a sales report using this Redis data:\n\n{data_json}""")

#     # If user asks for data inside Redis
#     if "data" in q_lower or "report" in q_lower or "content" in q_lower:
#         match = re.search(r'key[s]?\s*(matching|for|with)?\s*([a-z0-9:\-\*\?]+)', question, re.IGNORECASE)
#         if match:
#             pattern = match.group(2)
#             return get_keys_with_data(pattern)

#     # List Redis keys
#     match = re.search(r'keys?\s*(matching|for|with)?\s*([a-z0-9:\-\*\?]+)', question, re.IGNORECASE)
#     if match:
#         pattern = match.group(2)
#         return list_keys(pattern)

#     # Default: ask LLM
#     return ask_mistral(question)



#from resources.keys import list_keys, get_keys_with_data, extract_top_reports_only
# Adjust if defined elsewhere

# @mcp.tool()
# def auto_route(question: str) -> str:
#     q_lower = question.lower()

#     # Redis connection status
#     if "redis status" in q_lower or "is redis connected" in q_lower or "redis connection" in q_lower:
#         return _connection_status()

#     # Match key patterns in the question
#     key_match = re.search(r'key[s]?\s*(matching|for|with)?\s*([a-z0-9:\-\*\?]+)', question, re.IGNORECASE)
#     if key_match:
#         pattern = key_match.group(2)

#         # If the question is about generating a business report
#         if "generate report" in q_lower or "business report" in q_lower:
#             raw_json = get_keys_with_data(pattern)
#             parsed = json.loads(raw_json)

#             # Extract first valid key's data
#             if isinstance(parsed, dict) and parsed:
#                 first_val = list(parsed.values())[0]
#                 trimmed_data = extract_top_reports_only(first_val, top_n=2)
#                 return ask_mistral(
#                     f"You are a business analyst. Generate a sales report based on this data:\n\n{trimmed_data}"
#                 )
#             else:
#                 return "No valid data found to generate the report."

#         # If user just asks for raw report/data
#         elif "data" in q_lower or "report" in q_lower or "content" in q_lower:
#             return get_keys_with_data(pattern)

#         # Otherwise just list keys
#         else:
#             return list_keys(pattern)

#     # Fallback to LLM for general questions
#     return ask_mistral(question)

@mcp.tool()
def debug_key(key: str) -> str:
    """Raw get Redis key and decode it."""
    val = redis_client.get(key)
    if not val:
        return f"❌ No data found for key: {key}"
    
    try:
        decoded = val.decode("utf-8") if isinstance(val, bytes) else val
        try:
            parsed = json.loads(decoded)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            return f"📝 Raw String: {decoded}"
    except Exception as e:
        return f"⚠️ Error decoding value: {e}"


@mcp.tool()
def test_scan_keys(pattern: str) -> list:
    """List raw Redis keys that match a pattern."""
    return [k.decode() if isinstance(k, bytes) else k for k in redis_client.scan_iter(pattern)]



@mcp.tool()
def extract_top_reports_only(data: dict, top_n: int = 2) -> str:
    """Extract top N reports from all dashboards with current & previous data."""
    reports_data = []
    dashboards = data.get("dashboards", [])

    for dash in dashboards:
        for rep in dash.get("reports", []):
            report_entry = {
                "dashboard": dash.get("dashboardName"),
                "report": rep.get("reportName"),
                "current": rep.get("reportType", {}).get("data", {}).get("reportDataCurrent"),
                "previous": rep.get("reportType", {}).get("data", {}).get("reportDataPrevious"),
            }
            reports_data.append(report_entry)

            # Stop if we have collected enough
            if len(reports_data) >= top_n:
                return json.dumps(reports_data, indent=2)

    return json.dumps(reports_data, indent=2)


@mcp.tool()
def get_keys_with_data(key_pattern: str) -> str:
    """
    Search Redis for keys matching the given pattern and return their values.
    This works for string keys storing JSON data.
    """
    import fnmatch

    # Find matching keys
    all_keys = redis_client.keys("*")
    matching_keys = [k.decode() if isinstance(k, bytes) else k for k in all_keys if fnmatch.fnmatch(k.decode() if isinstance(k, bytes) else k, key_pattern)]

    if not matching_keys:
        return f"❌ No keys match pattern: {key_pattern}"

    result = {}
    for key in matching_keys:
        raw = redis_client.get(key)
        if raw:
            try:
                decoded = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                try:
                    parsed = json.loads(decoded)
                    result[key] = parsed
                except json.JSONDecodeError:
                    result[key] = decoded
            except Exception as e:
                result[key] = f"⚠️ decode error: {e}"
        else:
            result[key] = "❌ No data"

    return json.dumps(result, indent=2)


import re
import json

@mcp.tool()
def auto_route(question: str) -> str:
    """
    Smart router to:
    - Check Redis connection
    - List keys matching pattern
    - Get raw Redis string key data (parsed if JSON)
    - Generate a business report if the structure supports it
    - Or fallback to Mistral for general queries
    """
    q_lower = question.lower()

    # 1. Redis connection check
    if "redis status" in q_lower or "is redis connected" in q_lower or "redis connection" in q_lower:
        return _connection_status()

    # 2. Extract key pattern (e.g., user-reports:* or sales:store-1:*)
    key_match = re.search(r'key[s]?\s*(matching|for|with)?\s*([a-z0-9:\-\*\?]+)', q_lower, re.IGNORECASE)
    if not key_match:
        return ask_mistral(question)  # No pattern found, fallback

    pattern = key_match.group(2)

    # 3. Try fetching data
    raw_json = get_keys_with_data(pattern)

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return "❌ Error: Invalid JSON format in Redis data."

    if not isinstance(parsed, dict) or not parsed:
        return f"⚠️ No valid data found for keys matching: {pattern}"

    # 4. If user asked for report generation
    if "generate report" in q_lower or "business report" in q_lower:
        for val in parsed.values():
            if isinstance(val, dict) and "dashboards" in val:
                trimmed = extract_top_reports_only(val, top_n=2)
                return ask_mistral(
                    f"""You are a business analyst. Generate a concise sales report based on the following reports data:\n\n{trimmed}"""
                )
        return "⚠️ No structured dashboards found to generate report."

    # 5. If user asked to view data
    if "report" in q_lower or "data" in q_lower or "content" in q_lower or "show" in q_lower:
        return json.dumps(parsed, indent=2)

    # 6. If user asked only for key list
    if "list" in q_lower or "key" in q_lower or "keys" in q_lower:
        return list_keys(pattern)

    # 7. Fallback
    return ask_mistral(question)

# ----------------------- Imports -----------------------
from typing import Dict, Union, Any
from redis.exceptions import RedisError

from mcp.types import TextContent, ToolAnnotations  # Removed 'Content' (not available)
from server import mcp
from connection import redis_client
from azure.ai.inference.models import UserMessage, SystemMessage

# ----------------------- Safe JsonType -----------------------
JsonType = Union[str, int, float, bool, None, list, dict[str, Any]]  # ✅ safe & stable


# ----------------------- Redis JSON Tools -----------------------

@mcp.tool()
async def json_set(name: str, path: str, value: JsonType, expire_seconds: int = None) -> str:
    """Set a JSON value in Redis at a given path with optional expiration."""
    try:
        redis_client.json().set(name, path, value)
        if expire_seconds:
            redis_client.expire(name, expire_seconds)
        return f"✅ JSON value set at path '{path}' in '{name}'." + (
            f" Expires in {expire_seconds} seconds." if expire_seconds else "")
    except RedisError as e:
        return f"❌ Error setting JSON value at path '{path}' in '{name}': {str(e)}"


@mcp.tool()
async def json_get(name: str, path: str = '$') -> str:
    """Get a JSON value from Redis at the given path."""
    try:
        value = redis_client.json().get(name, path)
        return str(value) if value else f"⚠️ No data found at path '{path}' in '{name}'."
    except RedisError as e:
        return f"❌ Error retrieving JSON value at path '{path}' in '{name}': {str(e)}"


@mcp.tool()
async def json_del(name: str, path: str = '$') -> str:
    """Delete a JSON value from Redis at the given path."""
    try:
        deleted = redis_client.json().delete(name, path)
        return f"🗑️ Deleted JSON at path '{path}' in '{name}'." if deleted else f"⚠️ No value found at '{path}' in '{name}'."
    except RedisError as e:
        return f"❌ Error deleting JSON value at path '{path}' in '{name}': {str(e)}"


##"What is the Redis status?" or "Is Redis connected?"
#"Give me keys matching user-*"
##Give me data of key matching user-reports:744E8A80-2F7C-426B-8D6D-02D177B4F2BD:20250601-20250607-20250501-20250507
## Generate report for key matching user-reports:..."
##Generate report for key matching  user-reports:744E8A80-2F7C-426B-8D6D-02D177B4F2BD:20250601-20250607-20250501-20250507

# -----------------------------------------------------------------------------------
# async def main():
#     print("✅ MCP Server is ready with Redis and Azure Mistral integration.")
#     await mcp.run()


# if __name__ == "__main__":
#     asyncio.run(main())



if __name__ == "__main__":
    print("✅ MCP Server is ready with Redis and Azure Mistral integration.")
    
    import uvicorn
    uvicorn.run(mcp.asgi, host="0.0.0.0", port=8080, reload=True)
