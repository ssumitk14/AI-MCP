import json
import os
import httpx
import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("company-bots")

API_BASE_URL = "http://127.0.0.1:8000"

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="ask_intranet_bot",
            description="Ask the intranet bot questions about company policies, PTO, leave, remote work, WFH, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to ask the intranet bot."
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="ask_finance_bot",
            description="Ask the finance bot questions about company revenue, financial performance, expenses, budgets, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to ask the finance bot."
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="calculator",
            description="A basic calculator that evaluates mathematical expressions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')."
                    }
                },
                "required": ["expression"]
            }
        ),
        Tool(
            name="fetch_database",
            description="Retrieve all records from the local dummy JSON database.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="retrieve_memory",
            description="Retrieve the long-term chat history to remember past conversations or user details.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_knowledge_base",
            description="Search the company knowledge base for specific information (RAG scenario).",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Keywords or topic to search for in the knowledge base."
                    }
                },
                "required": ["topic"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution requests."""
    if name == "calculator":
        if "expression" not in arguments:
            raise ValueError("Missing 'expression' argument")
        try:
            # Using eval cautiously for a local isolated tool
            # In production, use a safer math parser or ast.literal_eval if possible
            # We restrict builtins to avoid arbitrary code execution
            result = eval(arguments["expression"], {"__builtins__": {}})
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error evaluating expression: {str(e)}")]

    if name == "fetch_database":
        try:
            with open("database.json", "r") as f:
                data = json.load(f)
            return [TextContent(type="text", text=json.dumps(data, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading database: {str(e)}")]

    if name == "retrieve_memory":
        try:
            if not os.path.exists("chat_history.json"):
                return [TextContent(type="text", text="No past chat history found.")]
            with open("chat_history.json", "r") as f:
                history = json.load(f)
            return [TextContent(type="text", text=json.dumps(history[-50:], indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading history: {str(e)}")]

    if name == "search_knowledge_base":
        if "topic" not in arguments:
            raise ValueError("Missing 'topic' argument")
        try:
            if not os.path.exists("knowledge_base.txt"):
                return [TextContent(type="text", text="Knowledge base file not found.")]
            topic = arguments["topic"].lower()
            results = []
            with open("knowledge_base.txt", "r") as f:
                paragraphs = f.read().split("\n\n")
                for p in paragraphs:
                    if topic in p.lower():
                        results.append(p.strip())
            
            if not results:
                return [TextContent(type="text", text=f"No information found for topic: {topic}")]
            return [TextContent(type="text", text="\n\n".join(results))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading knowledge base: {str(e)}")]

    if name in ["ask_intranet_bot", "ask_finance_bot"]:
        if "query" not in arguments:
            raise ValueError("Missing 'query' argument")

        endpoint = "/chat/intranet" if name == "ask_intranet_bot" else "/chat/finance"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{API_BASE_URL}{endpoint}", json={"query": arguments["query"]})
                response.raise_for_status()
                data = response.json()
                return [TextContent(type="text", text=data.get("response", "Error: No response from bot."))]
            except Exception as e:
                return [TextContent(type="text", text=f"Error connecting to bot API: {str(e)}")]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
