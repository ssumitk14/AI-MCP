import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# We use the official OpenAI library
from openai import AsyncOpenAI

load_dotenv()

def save_to_history(role, content):
    history = []
    if os.path.exists("chat_history.json"):
        try:
            with open("chat_history.json", "r") as f:
                history = json.load(f)
        except Exception:
            pass
    
    # We only save text content to keep it clean
    if content.strip():
        history.append({"role": role, "content": content})
        with open("chat_history.json", "w") as f:
            json.dump(history, f, indent=2)

async def interactive_loop():
    # Configure the StdioServerParameters to run our local mcp_server.py
    # We use the python executable from our venv if available, or just 'python'
    python_path = "venv/bin/python" if os.path.exists("venv/bin/python") else "python"
    
    server_params = StdioServerParameters(
        command=python_path,
        args=["mcp_server_fast.py"],
        env=None
    )

    print("Starting MCP Client and connecting to local tool server...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected to MCP server successfully.")
                
                # Check tools
                tools_response = await session.list_tools()
                
                mcp_tools = []
                for t in tools_response.tools:
                    mcp_tools.append({
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema
                        }
                    })
                
                print(f"Loaded {len(mcp_tools)} tools from MCP server.")
                
                # Initialize OpenAI client 
                # (You must set OPENAI_API_KEY in the environment or .env file)
                if not os.getenv("OPENAI_API_KEY"):
                    print("\nError: OPENAI_API_KEY is not set. Please set it in your environment or a .env file.")
                    return
                    
                openai_client = AsyncOpenAI()
                
                base_system_prompt = {"role": "system", "content": "You are an agentic assistant operating with ZERO short-term memory. You cannot remember the previous conversation loop! If the user asks a follow-up question, uses a pronoun (he/it), or refers to past context, you MUST immediately call the 'retrieve_memory' tool to fetch the chat history before you answer. DO NOT GUESS."}
                
                print("--------------------------------------------------")
                print("Chat started. Type 'quit' or 'exit' to stop.")
                while True:
                    user_input = input("\nYou: ")
                    if user_input.lower() in ("quit", "exit"):
                        break
                        
                    # ZERO HISTORY CONTEXT WINDOW: Start absolutely fresh every single turn
                    messages = [
                        base_system_prompt,
                        {"role": "user", "content": user_input}
                    ]
                    
                    try:
                        # Call LLM with tools
                        response = await openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=messages,
                            tools=mcp_tools
                        )
                        
                        response_message = response.choices[0].message
                        
                        # Process any tool calls
                        if response_message.tool_calls:
                            messages.append(response_message)
                            for tool_call in response_message.tool_calls:
                                tool_name = tool_call.function.name
                                tool_args = json.loads(tool_call.function.arguments)
                                
                                print(f"[Calling tool: {tool_name} with {tool_args}]")
                                
                                # Call the tool from MCP server
                                tool_result = await session.call_tool(tool_name, tool_args)
                                
                                # Parse result
                                content_list = [c.text for c in tool_result.content if getattr(c, 'type', '') == 'text']
                                result_text = "\n".join(content_list)
                                
                                print(f"[Tool Result: {result_text}]")
                                
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": result_text
                                })
                                
                            # Get final response from LLM
                            final_response = await openai_client.chat.completions.create(
                                model="gpt-4o",
                                messages=messages
                            )
                            final_msg = final_response.choices[0].message.content
                            messages.append({"role": "assistant", "content": final_msg})
                            
                            # Save the entire completed turn to long-term memory at the end
                            save_to_history("user", user_input)
                            save_to_history("assistant", final_msg)
                            
                            print(f"\nAssistant: {final_msg}")

                        else:
                            # No tool calls
                            messages.append({"role": "assistant", "content": response_message.content})
                            
                            # Save the entire completed turn to long-term memory at the end
                            save_to_history("user", user_input)
                            save_to_history("assistant", response_message.content)
                            
                            print(f"\nAssistant: {response_message.content}")
                            
                    except Exception as e:
                        print(f"Error communicating with LLM: {e}")
                        messages.pop() # Remove the user input so we can retry

    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_loop())
