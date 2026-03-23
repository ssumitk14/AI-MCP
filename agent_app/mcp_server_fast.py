import json
import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("company-bots")
API_BASE_URL = "http://127.0.0.1:8000"

@mcp.tool()
async def ask_intranet_bot(query: str) -> str:
    """Ask the intranet bot questions about company policies, PTO, leave, remote work, WFH, etc."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE_URL}/chat/intranet", json={"query": query})
            response.raise_for_status()
            data = response.json()
            return data.get("response", "Error: No response from bot.")
        except Exception as e:
            return f"Error connecting to bot API: {str(e)}"

@mcp.tool()
async def ask_finance_bot(query: str) -> str:
    """Ask the finance bot questions about company revenue, financial performance, expenses, budgets, etc."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE_URL}/chat/finance", json={"query": query})
            response.raise_for_status()
            data = response.json()
            return data.get("response", "Error: No response from bot.")
        except Exception as e:
            return f"Error connecting to bot API: {str(e)}"

@mcp.tool()
async def calculator(expression: str) -> str:
    """A basic calculator that evaluates mathematical expressions. For example: '2 + 2', '10 * 5'."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

@mcp.tool()
async def fetch_database() -> str:
    """Retrieve all employee records (names, roles, departments) from the local database. Use this tool any time you are asked about specific people or employees."""
    try:
        with open("database.json", "r") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error reading database: {str(e)}"

@mcp.tool()
async def retrieve_memory(topic: str = "", count: int = 5) -> str:
    """Retrieve the long-term chat history. Use this any time you need to remember past conversation context. You can optionally provide a topic to filter by keyword, or just retrieve the last 'count' messages to get immediate chronological context."""
    try:
        if not os.path.exists("chat_history.json"):
            return "No past chat history found."
        with open("chat_history.json", "r") as f:
            history = json.load(f)
            
        if topic:
            topic = topic.lower()
            filtered = [m for m in history if topic in m.get("content", "").lower()]
            return json.dumps(filtered[-count:], indent=2)
        else:
            return json.dumps(history[-count:], indent=2)
    except Exception as e:
        return f"Error reading history: {str(e)}"

@mcp.tool()
async def search_knowledge_base(topic: str) -> str:
    """Search the company knowledge base for information on company history, core products, values, culture, and facilities (RAG scenario). Do NOT use this for employee lookup."""
    try:
        if not os.path.exists("knowledge_base.txt"):
            return "Knowledge base file not found."
        topic = topic.lower()
        results = []
        with open("knowledge_base.txt", "r") as f:
            paragraphs = f.read().split("\n\n")
            for p in paragraphs:
                if topic in p.lower():
                    results.append(p.strip())
        
        if not results:
            return f"No information found for topic: {topic}"
        return "\n\n".join(results)
    except Exception as e:
        return f"Error reading knowledge base: {str(e)}"

if __name__ == "__main__":
    # mcp.run() uses standard Stdio transport by default when executed directly
    mcp.run(transport="stdio")
