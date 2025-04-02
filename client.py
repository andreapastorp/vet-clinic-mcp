import asyncio
import json
import ssl
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

import anthropic
import httpx
import urllib3
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
API_KEY = os.environ.get("ANTHROPIC_API_KEY")

class VetClaudeClient:
    """Client for interacting with Claude and the Vet Clinic MCP server."""
    
    def __init__(self, server_path: str = "server.py"):
        """
        Initialize the client.
        
        Args:
            server_path: Path to the MCP server script
        """
        # Initialize Claude client with SSL certificate handling
        if not API_KEY:
            raise ValueError("Please set ANTHROPIC_API_KEY environment variable")
        
        # Create a custom httpx client with SSL verification disabled for development
        http_client = httpx.Client(
            verify=False,  # Disable SSL verification for development
            timeout=90.0   # Increased timeout
        )
        
        # Suppress SSL warnings (since we're disabling verification)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.claude = anthropic.Anthropic(
            api_key=API_KEY,
            http_client=http_client
        )
        
        # Initialize MCP server parameters
        self.server_path = server_path
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_path],
            env=None
        )
    
    async def chat_session(self):
        """Start an interactive chat session with Claude using the MCP server."""
        # Connect to the MCP server
        async with stdio_client(self.server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                print("Connected to Vet Clinic MCP server")
                
                # Get available tools
                tools_result = await session.list_tools()
                tools = []
                for tool in tools_result.tools:
                    tool_obj = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    tools.append(tool_obj)
                
                print(f"Loaded {len(tools)} tools from the server")
                
                # Initialize conversation
                messages = [
                    {
                        "role": "user", 
                        "content": "I'm a veterinarian using a practice management system. I need your help to access and manage patient data."
                    }
                ]
                
                # System prompt (must be passed separately, not as a message)
                system_prompt = "You are a veterinary assistant AI helping with a Veterinary Practice Management System. You have access to patient data and can perform operations like creating and updating patient records, adding appointments, and recording weight and vaccination information. Provide succinct answers to the information requested by the user."
                
                # First response from Claude
                initial_response = self.claude.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    system=system_prompt,  # System prompt as a separate parameter
                    messages=messages,
                    max_tokens=1000
                )
                
                # Display Claude's initial response
                initial_text = initial_response.content[0].text
                print(f"\nClaude: {initial_text}")
                
                # Add Claude's response to the conversation
                messages.append({"role": "assistant", "content": initial_text})
                
                # Chat loop
                while True:
                    # Get user input
                    user_input = input("\nYou: ")
                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("Ending session.")
                        break
                    
                    # Add user message to conversation
                    messages.append({"role": "user", "content": user_input})
                    
                    # Send to Claude
                    response = self.claude.messages.create(
                        model="claude-3-5-sonnet-20240620",  # Using a newer model
                        system=system_prompt,  # System prompt as a separate parameter
                        messages=messages,
                        tools=tools,
                        max_tokens=1000
                    )
                    
                    # Process Claude's response
                    for content in response.content:
                        if content.type == "text":
                            # Display Claude's text response
                            print(f"\nClaude: {content.text}")
                            messages.append({"role": "assistant", "content": content.text})
                        
                        elif content.type == "tool_use":
                            # Claude wants to use a tool
                            tool_name = content.name
                            tool_args = content.input
                            
                            print(f"\nClaude is using tool: {tool_name}")
                            print(f"With arguments: {json.dumps(tool_args, indent=2)}")
                            
                            # Execute the tool
                            try:
                                result = await session.call_tool(tool_name, tool_args)
                                tool_result = "Tool execution failed."
                                
                                # Extract the text result
                                for item in result.content:
                                    if hasattr(item, 'text'):
                                        tool_result = item.text
                                
                                # Show tool result
                                print(f"\nTool result: {tool_result}")
                                
                                # Add tool use to conversation history properly
                                # First the assistant's tool use
                                messages.append({
                                    "role": "assistant",
                                    "content": [
                                        {
                                            "type": "tool_use", 
                                            "id": content.id, 
                                            "name": tool_name, 
                                            "input": tool_args
                                        }
                                    ]
                                })
                                
                                # Then the tool result from user
                                messages.append({
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result", 
                                            "tool_use_id": content.id, 
                                            "content": tool_result
                                        }
                                    ]
                                })
                                
                                # Get Claude's response after tool use
                                tool_response = self.claude.messages.create(
                                    model="claude-3-5-sonnet-20240620", 
                                    system=system_prompt,  # System prompt as a separate parameter
                                    messages=messages,
                                    max_tokens=1000
                                )
                                
                                # Extract and display Claude's response to the tool result
                                for tool_content in tool_response.content:
                                    if tool_content.type == "text":
                                        print(f"\nClaude: {tool_content.text}")
                                        messages.append({"role": "assistant", "content": tool_content.text})
                                        
                            except Exception as e:
                                error_message = f"Error executing tool: {str(e)}"
                                print(f"\nError: {error_message}")
                                
                                # Inform Claude about the error
                                messages.append({
                                    "role": "assistant", 
                                    "content": [
                                        {"type": "tool_use", "id": content.id, "name": tool_name, "input": tool_args}
                                    ]
                                })
                                messages.append({
                                    "role": "user", 
                                    "content": [
                                        {
                                            "type": "tool_result", 
                                            "tool_use_id": content.id, 
                                            "content": f"Error: {error_message}"
                                        }
                                    ]
                                })
                
                print("\nDisconnected from Vet Clinic MCP server")


async def main():
    """Run the Claude + MCP client."""
    # First make sure the database exists
    from init import init_db
    init_db()
    
    # Create and run client
    client = VetClaudeClient()
    await client.chat_session()


if __name__ == "__main__":
    asyncio.run(main())
