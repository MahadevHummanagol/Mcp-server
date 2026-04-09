
# client.py

import asyncio
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import AssistantMessage, SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# === Azure Mistral Config ===
AZURE_ENDPOINT = "https://Mistral-Large-2411-"
AZURE_KEY = '
AZURE_MODEL = "Mistral-Large-2411-clhld"

client = ChatCompletionsClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY),
    api_version="2024-05-01-preview"
)

# Dummy summary data to simulate dashboard JSON summary
summary_dict = {
    "sales_summary.json": "Total sales vs previous period by category and store",
    "profit_margin.json": "Gross margin trends by top-selling products",
    "wastage_report.json": "Wastage percentage by SKU and location",
}

# === Sampling handler ===
async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    try:
        user_question = message.content.text
        tool_name = message.tool or ""

        # Customize prompt based on which tool is calling (optional)
        if tool_name == "ask_mistral":
            report_list = "\n".join([f"{k}: {v}" for k, v in summary_dict.items()])
            system_prompt = f'''
You are an intelligent assistant that selects the most relevant report(s) from a dashboard JSON summary based on a user's business question.

Each report includes schema of data:
- report name
- brief description
- type of chart
- key fields in the current and previous period data

Your task is to analyze the user's question and select the **most relevant report names** (not file paths) from the list provided and schema of data. Return keys as a Python list of file names. Do not explain.

User question: "{user_question}"
'''

            response = client.complete(
                messages=[
                    SystemMessage(content=system_prompt),
                    UserMessage(content=f"Here are the available reports:\n{report_list}")
                ],
                max_tokens=1024,
                temperature=0.3,
                model=AZURE_MODEL
            )

            return types.CreateMessageResult(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text=response.choices[0].message.content
                ),
                model="mistral-azure",
                stopReason="endTurn"
            )

        else:
            # Fallback prompt logic
            response = client.complete(
                messages=[
                    UserMessage(content=user_question)
                ],
                max_tokens=512,
                temperature=0.7,
                model=AZURE_MODEL
            )

            return types.CreateMessageResult(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text=response.choices[0].message.content
                ),
                model="mistral-azure",
                stopReason="endTurn"
            )

    except Exception as e:
        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(
                type="text",
                text=f"[ERROR] Mistral integration failed: {str(e)}"
            ),
            model="mistral-azure",
            stopReason="error"
        )

# === Stdio server parameters ===
server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
    env=None,
)

# === Main runner ===
async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=handle_sampling_message) as session:
            await session.initialize()
            print("✅ MCP session initialized with Azure Mistral")
            prompts = await session.list_prompts()
            print("📄 Available prompts:", prompts)

if __name__ == "__main__":
    asyncio.run(run())
