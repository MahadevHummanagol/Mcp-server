# ----------------------- Azure & Redis Setup -----------------------
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import AssistantMessage, SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from redis import Redis
from redis.exceptions import RedisError
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ToolAnnotations
from connection import redis_client
from resources.status import connection_status, redis_info
import json
import fnmatch
import re
from typing import Dict, Union, Any

import os
import json
import logging
from datetime import datetime
import time
import logging
from datetime import datetime
import os

# Create a logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Unique log filename per session (or daily)
log_filename = f"logs/mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("🟢 Logging system initialized.")


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

# Azure Mistral Configuration
AZURE_ENDPOINT = "https://Mistral-Large-2411-clhld.--------------
AZURE_KEY = "-----------------"
AZURE_MODEL = "Mistral-Large-2411-clhld"

# Create client
mistral_client = ChatCompletionsClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY),
    api_version="2024-05-01-preview"
)


# ✅ Enables /mcp endpoint
mcp = FastMCP("MahadevDemo 🚀", stateless_http=True, json_response=True)

# @mcp.tool()
# def mango()

@mcp.tool()
def ask_with_data(question: str) -> str:
    start_time = time.time()
    logging.info(f"📥 Question received: {question}")

    from tiktoken import get_encoding
    encoding = get_encoding("cl100k_base")

    # Step 1: Load dashboards
    try:
        dashboards_data = redis_client.json().get(
            "user-reports:744E8A80-2F7C-426B-8D6D-02D177B4F2BD:eJwzNDAwBAAB6QDD:20250601-20250617",
            "$.dashboards[*]"
        )
        logging.info("✅ Dashboards successfully loaded from Redis.")
    except RedisError as e:
        logging.error(f"❌ Redis Error: {str(e)}")
        return f"❌ Redis Error: {str(e)}"

    if not dashboards_data:
        logging.warning("⚠️ No dashboards found in Redis.")
        return "⚠️ No dashboards found."

    # Step 2: Build report catalog
    report_catalog = []
    for dashboard in dashboards_data:
        for report in dashboard.get("reports", []):
            report_catalog.append({
                "dashboardName": dashboard.get("dashboardName"),
                "reportName": report.get("reportName"),
                "reportDescription": report.get("reportDescription", "No description"),
                "data": report.get("reportType", {}).get("data", {})
            })
    logging.info(f"📊 Reports cataloged: {len(report_catalog)} reports found.")

    # Step 3: Use LLM to select reports
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
    logging.info(f"🧠 LLM selected reports: {selected_names}")

    if not selected_names:
        logging.warning("⚠️ LLM did not select any reports.")
        return "⚠️ LLM could not select any reports."

    # Step 4: Combine data
    combined_data_blocks = []
    for r in report_catalog:
        if r["reportName"] in selected_names:
            combined_data_blocks.append({
                "reportName": r["reportName"],
                "data": r["data"]
            })
    json_string = json.dumps(combined_data_blocks)
    num_tokens = len(encoding.encode(json_string))
    logging.info(f"📦 Combined data blocks: {len(combined_data_blocks)} | Tokens: {num_tokens}")

    MAX_TOKENS_FOR_CONTEXT = 3000
    if num_tokens > MAX_TOKENS_FOR_CONTEXT:
        logging.warning(f"⚠️ Selected report data too large ({num_tokens} tokens).")
        return f"⚠️ Selected report data is too large ({num_tokens} tokens). Please refine your question."

    # Step 5: Final prompt
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
    output = final_response.choices[0].message.content.strip()
    logging.info("✅ Final response generated by Mistral.")
    logging.info(f"📤 Output:\n{output}")

    end_time = time.time()
    duration = round(end_time - start_time, 2)
    logging.info(f"⏱️ Total time taken: {duration} seconds")

    return output


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

