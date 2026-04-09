#C:\mcp-server-demo\resources\keys.py

# from mcp.server.fastmcp import FastMCP
import json
import json
from connection import redis_client

# # @mcp.resource("redis://keys/{pattern}")
# # def list_keys(pattern: str) -> str:
# #     """List Redis keys matching a pattern"""
# #     try:
# #         keys = redis_client.keys(pattern)
# #         return json.dumps({"keys": keys}, indent=2)
# #     except Exception as e:
# #         return json.dumps({"error": str(e)})
# import json
# from connection import redis_client

def list_keys(pattern: str) -> str:
    try:
        keys = redis_client.keys(pattern)
        decoded_keys = []
        for key in keys:
            # Decode only if bytes, else keep as is
            if isinstance(key, bytes):
                decoded_keys.append(key.decode("utf-8"))
            else:
                decoded_keys.append(key)
        return json.dumps({"keys": decoded_keys}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})




# def extract_top_reports_only(data: dict, top_n: int = 2) -> str:
#     reports_data = []
#     dashboards = data.get("dashboards", [])

#     count = 0
#     for dash in dashboards:
#         for rep in dash.get("reports", []):
#             reports_data.append({
#                 "dashboard": dash.get("dashboardName"),
#                 "report": rep.get("reportName"),
#                 "current": rep.get("reportType", {}).get("data", {}).get("reportDataCurrent"),
#                 "previous": rep.get("reportType", {}).get("data", {}).get("reportDataPrevious"),
#             })
#             count += 1
#             if count >= top_n:
#                 return json.dumps(reports_data, indent=2)

#     return json.dumps(reports_data, indent=2)


