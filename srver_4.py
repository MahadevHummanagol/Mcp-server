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
# ----------------------- Imports -----------------------
from typing import Dict, Union, Any
from redis.exceptions import RedisError

from mcp.types import TextContent, ToolAnnotations  # Removed 'Content' (not available)
from server import mcp
from connection import redis_client
from azure.ai.inference.models import UserMessage, SystemMessage

from redis import Redis
from redis.exceptions import RedisError

# Connect to Redis (corrected arguments)
redis_client = Redis(
    host="redis-14634.c251.east-us-mz.azure.redns.redis-cloud.com",
    port=14634,
    username="default",
    password="68mOAf810GLVydSErlyTNn5tJJnmLYAJ",
    decode_responses=True
)

# ----------------------- Safe JsonType -----------------------
JsonType = Union[str, int, float, bool, None, list, dict[str, Any]]  # ✅ safe & stable


# ----------------------- Redis JSON Tools -----------------------
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



# ✅ Enables /mcp endpoint
mcp = FastMCP("MahadevDemo 🚀", stateless_http=True, json_response=True)


@mcp.tool()
def ask_with_data(question: str) -> str:
    """
    Ask a business question to Mistral.
    Automatically selects the right reports from Redis,
    combines their data, and sends the question + data to Mistral for analysis.
    """
    from tiktoken import get_encoding
    encoding = get_encoding("cl100k_base")

    # Step 1: Load dashboards and all reports from Redis
    try:
        dashboards_data = redis_client.json().get(
            "user-reports:744E8A80-2F7C-426B-8D6D-02D177B4F2BD:eJwzNDAwBAAB6QDD:20250605-20250616-20250501-20250516",
            "$.dashboards[*]"
        )
    except RedisError as e:
        return f"❌ Redis Error: {str(e)}"

    if not dashboards_data:
        return "⚠️ No dashboards found."

    # Step 2: Build list of all reports (name, description)
    report_catalog = []
    for dashboard in dashboards_data:
        for report in dashboard.get("reports", []):
            report_catalog.append({
                "dashboardName": dashboard.get("dashboardName"),
                "reportName": report.get("reportName"),
                "reportDescription": report.get("reportDescription", "No description"),
                "data": report.get("reportType", {}).get("data", {})
            })

    # Step 3: Let Mistral LLM choose relevant reports
    catalog_summary = "\n".join([
        f"- {r['reportName']}: {r['reportDescription']}" for r in report_catalog
    ])
    
    selection_prompt = (
        "You are a business analyst selecting which sales reports are most relevant "
        "to answer a business user's question. Here is the question:\n\n"
        f"{question}\n\n"
        "Here is a list of available reports:\n"
        f"{catalog_summary}\n\n"
        "Return ONLY a list of report names (exact match) that are relevant. Do not explain or justify."
    )
    
    selection_response = mistral_client.complete(
        messages=[
            SystemMessage(content="You are a smart report selector. Always return a plain list of report names."),
            UserMessage(content=selection_prompt)
        ],
        model=AZURE_MODEL,
        max_tokens=256,
        temperature=0.1,
    )
    
    selected_names = [
        line.strip("- ").strip()
        for line in selection_response.choices[0].message.content.strip().splitlines()
        if line.strip()
    ]
    if not selected_names:
        return "⚠️ LLM could not select any reports."

    # Step 4: Combine selected reports
    combined_data_blocks = []
    for r in report_catalog:
        if r["reportName"] in selected_names:
            combined_data_blocks.append({
                "reportName": r["reportName"],
                "data": r["data"]
            })

    # Step 5: Limit combined data size using token budget
    json_string = json.dumps(combined_data_blocks)
    num_tokens = len(encoding.encode(json_string))
    MAX_TOKENS_FOR_CONTEXT = 3000

    if num_tokens > MAX_TOKENS_FOR_CONTEXT:
        return f"⚠️ Selected report data is too large ({num_tokens} tokens). Please refine your question."

    # Step 6: Final prompt to Mistral
    final_prompt = (
        "Here is a list of data blocks from selected sales reports. "
        "Answer the business question based ONLY on the data and not on any assumptions.\n\n"
        f"Question:\n{question}\n\n"
        f"Data:\n{json_string}"
    )

    final_response = mistral_client.complete(
        messages=[
            SystemMessage(content='''You are a subject matter expert, a data analyst and a business expert who has been running all types of retail chains and restaurant chains and are an advisor to a lot of these chains. 
You always provide your answers in a concise manner, by providing insights in the form of three sections - analysis, recommendations and anomalies. All these sections always have 3 bullet points of the most important insights put very concisely that are very easy to understand for the business owner.
You never give vague responses and make your responses very specific and accurate according to the data in the project files. Do not provide any insights related to technology, as I don't have control over those calculations.'''),
            UserMessage(content=final_prompt)
        ],
        model=AZURE_MODEL,
        max_tokens=1024,
        temperature=0.3,
    )

    return final_response.choices[0].message.content.strip()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")


