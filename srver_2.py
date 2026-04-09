from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import AssistantMessage, SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from connection import redis_client
from resources.status import connection_status, redis_info

from mcp.server.fastmcp import FastMCP
import json
from resources.status import connection_status, redis_info
from connection import redis_client
import fnmatch

from mcp.server.fastmcp import FastMCP
import re
import json
 
# ✅ Enables /mcp endpoint
mcp = FastMCP("MahadevDemo 🚀", stateless_http=True, json_response=True)

# Azure Mistral Configuration
AZURE_ENDPOINT = "https://Mistral-Large-2411-clhld.southcentralus.models.ai.azure.com"
AZURE_KEY = "5WCo1nlf7qfaEr7BEHdW9KWR3k8dvnNu"
AZURE_MODEL = "Mistral-Large-2411-clhld"

# Create client
mistral_client = ChatCompletionsClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY),
    api_version="2024-05-01-preview"
)


@mcp.tool()
async def greet(name: str) -> str:
    return f"Hello, {name}!"

@mcp.tool(description="Add two to a given number")
async def add_two(n: int) -> int:
    return n + 2

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

# @mcp.tool(description="Get a value from Redis by key")
# def get_redis_value(key: str) -> str:
#     value = redis_client.get(key)
#     if value is None:
#         return f"No value found for key: {key}"
#     try:
#         # Attempt to decode JSON if it's JSON-encoded
#         return json.dumps(json.loads(value), indent=2)
#     except Exception:
#         return value.decode("utf-8") if isinstance(value, bytes) else str(value)

@mcp.tool()
def get_keys_with_pattern(key_pattern: str) -> str:
    """
    Search Redis for keys matching the given pattern and return their values.
    Handles different Redis data types safely.
    """
    all_keys = redis_client.keys("*")
    matching_keys = [
        k.decode() if isinstance(k, bytes) else k
        for k in all_keys
        if fnmatch.fnmatch(k.decode() if isinstance(k, bytes) else k, key_pattern)
    ]

    if not matching_keys:
        return f"❌ No keys match pattern: {key_pattern}"

    result = {}

    for key in matching_keys:
        try:
            key_type = redis_client.type(key).decode()

            if key_type == "string":
                raw = redis_client.get(key)
                val = raw.decode() if isinstance(raw, bytes) else raw
                try:
                    result[key] = json.loads(val)
                except json.JSONDecodeError:
                    result[key] = val

            elif key_type == "hash":
                result[key] = redis_client.hgetall(key)

            elif key_type == "list":
                result[key] = redis_client.lrange(key, 0, -1)

            elif key_type == "set":
                result[key] = list(redis_client.smembers(key))

            elif key_type == "zset":
                result[key] = redis_client.zrange(key, 0, -1, withscores=True)

            else:
                result[key] = f"⚠️ Unsupported Redis type: {key_type}"

        except Exception as e:
            result[key] = f"❌ Error: {str(e)}"

    return json.dumps(result, indent=2)



@mcp.tool()
def get_keys_with_data(key_pattern: str) -> str:
    """
    Fetch and decode values from Redis keys matching a pattern.
    Supports: string, hash, list, set, sorted set.
    """
    import fnmatch
    import json

    result = {}

    all_keys = redis_client.keys("*")
    matching_keys = [
        k.decode() if isinstance(k, bytes) else k
        for k in all_keys
        if fnmatch.fnmatch(k.decode() if isinstance(k, bytes) else k, key_pattern)
    ]

    if not matching_keys:
        return json.dumps({"error": f"No keys matched: {key_pattern}"}, indent=2)

    for key in matching_keys:
        try:
            key_type = redis_client.type(key)
            key_type = key_type.decode() if isinstance(key_type, bytes) else key_type

            if key_type == "string":
                val = redis_client.get(key)
                val = val.decode() if isinstance(val, bytes) else val
                print(f"🔍 Raw value for key '{key}':\n{val}")

                try:
                    # Try parsing the inner string as JSON
                    parsed = json.loads(val)
                    result[key] = parsed


                except json.JSONDecodeError as e:
                    # Keep as-is if not JSON
                    result[key] = {"_raw": val, "_error": f"❌ JSON parse error: {str(e)}"}

            else:
                result[key] = f"⚠️ Unsupported key type: {key_type}"

        except Exception as e:
            result[key] = f"❌ Error reading key: {str(e)}"

        

    # 🔥 This was missing
    return json.dumps(result, indent=2)


@mcp.tool(description="Check Redis connection status")
def check_redis_status() -> str:
    return connection_status()

@mcp.tool(description="Get full Redis server info")
def get_redis_server_info() -> str:
    return redis_info()



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

            if len(reports_data) >= top_n:
                return json.dumps(reports_data, indent=2)

    return json.dumps(reports_data, indent=2)


# @mcp.tool()
# def get_keys_with_data(key_pattern: str) -> str:
#     """Search Redis for keys matching the pattern and return their values."""
#     all_keys = redis_client.keys("*")
#     matching_keys = [
#         k.decode() if isinstance(k, bytes) else k
#         for k in all_keys
#         if fnmatch.fnmatch(k.decode() if isinstance(k, bytes) else k, key_pattern)
#     ]

#     if not matching_keys:
#         return f"❌ No keys match pattern: {key_pattern}"

#     result = {}
#     for key in matching_keys:
#         raw = redis_client.get(key)
#         if raw:
#             try:
#                 decoded = raw.decode("utf-8") if isinstance(raw, bytes) else raw
#                 try:
#                     parsed = json.loads(decoded)
#                     result[key] = parsed
#                 except json.JSONDecodeError:
#                     result[key] = decoded
#             except Exception as e:
#                 result[key] = f"⚠️ decode error: {e}"
#         else:
#             result[key] = "❌ No data"

#     return json.dumps(result, indent=2)


# Assuming you're using FastMCP

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
        return ask_mistral(question)  # No pattern found, fallback to LLM

    pattern = key_match.group(2)

    # 3. Fetch data from Redis for matching keys
    raw_json = get_keys_with_data(pattern)

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return "❌ Error: Invalid JSON format in Redis data."

    if not isinstance(parsed, dict) or not parsed:
        return f"⚠️ No valid data found for keys matching: {pattern}"

    # 4. Generate business report if applicable
    if "generate report" in q_lower or "business report" in q_lower:
        for val in parsed.values():
            if isinstance(val, dict) and "dashboards" in val:
                trimmed = extract_top_reports_only(val, top_n=2)
                return ask_mistral(
                    f"""You are a business analyst. Generate a concise sales report based on the following reports data:\n\n{trimmed}"""
                )
        return "⚠️ No structured dashboards found to generate report."

    # 5. Show raw data if user requested report/content/data
    if "report" in q_lower or "data" in q_lower or "content" in q_lower or "show" in q_lower:
        return json.dumps(parsed, indent=2)

    # 6. List only the keys
    if "list" in q_lower or "key" in q_lower or "keys" in q_lower:
        return list_keys(pattern)

    # 7. Default fallback to LLM
    return ask_mistral(question)





if __name__ == "__main__":
    mcp.run(transport="streamable-http")


