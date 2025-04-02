import asyncio
import os
import json
from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
# Import or initialize your anthropic client for Claude
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not set in environment")

claude = anthropic.Anthropic(api_key=API_KEY)

# MCP server parameters
server_params = StdioServerParameters(
    command="python",
    args=["backend/server.py"],
    env=None
)

async def get_all_patients():
    """Get all patients using MCP."""
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Get resource content as string
            content, _ = await session.read_resource("patients://all")
            
            # Process the content based on your specific implementation
            # This is just an example - adjust based on your actual data format
            patients = []
            for line in content.strip().split('\n')[1:]:  # Skip header
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 4:
                    patients.append({
                        'id': parts[0].strip(),
                        'name': parts[1].strip(),
                        'species': parts[2].strip(),
                        'breed': parts[3].strip(),
                    })
            
            return patients

async def get_patient_details(patient_id):
    """Get details for a specific patient."""
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Get resource content
            content, _ = await session.read_resource(f"patients://{patient_id}")
            
            # Parse the content based on your specific implementation
            lines = content.strip().split('\n')
            patient = {'id': patient_id}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    patient[key.strip().lower().replace(' ', '_')] = value.strip()
            
            return patient

async def create_patient(data):
    """Create a new patient."""
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Call the create_patient tool
            result = await session.call_tool(
                name="create_patient",
                arguments=data
            )
            
            # Extract text content from the result
            response_text = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    response_text = item.text
            
            return response_text

async def process_message(message):
    """Process a chat message with Claude using MCP tools."""
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Get available tools
            tools_result = await session.list_tools()
            tools = []
            for tool in tools_result.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            # System prompt
            system_prompt = "You are a veterinary assistant AI helping with a Veterinary Practice Management System. Provide concise answers based on the patient data available."
            
            # Send to Claude
            response = claude.messages.create(
                model="claude-3-5-sonnet-20240620",
                system=system_prompt,
                messages=[{"role": "user", "content": message}],
                tools=tools,
                max_tokens=1000
            )
            
            results = []
            
            # Process Claude's response
            for content in response.content:
                if content.type == "text":
                    results.append({
                        "type": "text",
                        "content": content.text
                    })
                
                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input
                    
                    # Execute the tool
                    try:
                        result = await session.call_tool(tool_name, tool_args)
                        tool_result = "Tool execution failed."
                        
                        # Extract the text result
                        for item in result.content:
                            if hasattr(item, 'text'):
                                tool_result = item.text
                        
                        # Add tool results
                        results.append({
                            "type": "tool",
                            "name": tool_name,
                            "args": tool_args,
                            "result": tool_result
                        })
                        
                        # Get Claude's response to the tool result
                        tool_response = claude.messages.create(
                            model="claude-3-5-sonnet-20240620",
                            system=system_prompt,
                            messages=[
                                {"role": "user", "content": message},
                                {"role": "assistant", "content": [{"type": "tool_use", "id": content.id, "name": tool_name, "input": tool_args}]},
                                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": content.id, "content": tool_result}]}
                            ],
                            max_tokens=1000
                        )
                        
                        # Add Claude's final response
                        if tool_response.content[0].type == "text":
                            results.append({
                                "type": "text",
                                "content": tool_response.content[0].text
                            })
                    
                    except Exception as e:
                        results.append({
                            "type": "error",
                            "content": f"Error executing tool: {str(e)}"
                        })
            
            return results
