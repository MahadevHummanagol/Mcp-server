from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import AssistantMessage, SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential


from mcp.server.fastmcp import FastMCP

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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")




#####################################################################################################################
# import requests
# import uuid

# URL = "http://127.0.0.1:8000/mcp/"

# headers = {
#     "Content-Type": "application/json",
#     "Accept": "application/json, text/event-stream"
# }

# payload = {
#     "jsonrpc": "2.0",
#     "id": str(uuid.uuid4()),
#     "method": "tools/call",
#     "params": {
#         "name": "add_two",
#         "arguments": {
#             "n": 5
#         }
#     }
# }

# response = requests.post(URL, json=payload, headers=headers)

# print("Status Code:", response.status_code)
# print("Response:", response.json())
########################################################################################
# import requests
# import uuid

# URL = "http://127.0.0.1:8000/mcp/"  # If you're running locally

# headers = {
#     "Content-Type": "application/json",
#     "Accept": "application/json, text/event-stream"
# }

# payload = {
#     "jsonrpc": "2.0",
#     "id": str(uuid.uuid4()),
#     "method": "tools/call",
#     "params": {
#         "name": "ask_mistral",
#         "arguments": {
#             "question": "What are the key insights from last week's restaurant sales?"
#         }
#     }
# }

# response = requests.post(URL, json=payload, headers=headers)

# print("Status Code:", response.status_code)
# print("Response:", response.json())
