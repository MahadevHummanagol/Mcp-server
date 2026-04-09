
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

@mcp.tool()
def get_keys_with_data(key_pattern: str = "*") -> str:
    """
    Fetch Redis key(s) matching a pattern.
    If pattern starts with 'recent:', only return the latest-matching key.
    Supports string keys with optional JSON decoding.
    """
    import fnmatch
    import json
    import re

    result = {}
    all_keys = redis_client.keys("*")
    decoded_keys = [k.decode() if isinstance(k, bytes) else k for k in all_keys]

    if key_pattern.startswith("recent:"):
        base_pattern = key_pattern.replace("recent:", "", 1)

        # Filter by pattern
        filtered_keys = [k for k in decoded_keys if fnmatch.fnmatch(k, base_pattern)]

        # Sort descending (assumes time info embedded lexically)
        sorted_keys = sorted(filtered_keys, reverse=True)

        if not sorted_keys:
            return json.dumps({"error": f"No recent key matched pattern: {base_pattern}"}, indent=2)

        matching_keys = [sorted_keys[0]]  # Only the most recent
    else:
        matching_keys = [k for k in decoded_keys if fnmatch.fnmatch(k, key_pattern)]

        if not matching_keys:
            return json.dumps({"error": f"No keys matched pattern: {key_pattern}"}, indent=2)

    # Fetch values
    for key in matching_keys:
        try:
            key_type = redis_client.type(key)
            key_type = key_type.decode() if isinstance(key_type, bytes) else key_type

            if key_type == "string":
                val = redis_client.get(key)
                val = val.decode() if isinstance(val, bytes) else val
                try:
                    parsed = json.loads(val)
                    result[key] = parsed
                except json.JSONDecodeError as e:
                    result[key] = {"_raw": val, "_error": f"❌ JSON parse error: {str(e)}"}
            else:
                result[key] = f"⚠️ Unsupported key type: {key_type}"

        except Exception as e:
            result[key] = f"❌ Error reading key: {str(e)}"

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")


