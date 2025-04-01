import asyncio
import json
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# Sample data - a very basic patient database
PATIENTS = [
    {
        "id": "P001",
        "name": "Kubba",
        "species": "Dog",
        "breed": "Golden Retriever",
        "age": 5,
        "owner": "Andrea Smith"
    },
    {
        "id": "P002",
        "name": "Bella",
        "species": "Cat",
        "breed": "Siamese",
        "age": 7,
        "owner": "Michael Johnson"
    },
    {
        "id": "P003",
        "name": "Max",
        "species": "Dog",
        "breed": "Beagle",
        "age": 3,
        "owner": "Sarah Williams"
    }
]

# Initialize FastMCP server
mcp = FastMCP("pims")

@mcp.tool()
async def get_patient(identifier: str) -> Dict[str, Any]:
    """Get information about a patient by name or ID.
    
    Args:
        identifier: Patient name or ID
        
    Returns:
        Dictionary with patient information or error message
    """
    for patient in PATIENTS:
        if patient["id"] == identifier or patient["name"].lower() == identifier.lower():
            return {
                "found": True,
                "patient": patient
            }
    
    return {
        "found": False,
        "message": f"No patient found with identifier: {identifier}"
    }

@mcp.tool()
async def list_patients() -> Dict[str, Any]:
    """List all patients in the database.
    
    Returns:
        Dictionary with count and list of all patients
    """
    return {
        "count": len(PATIENTS),
        "patients": PATIENTS
    }

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
