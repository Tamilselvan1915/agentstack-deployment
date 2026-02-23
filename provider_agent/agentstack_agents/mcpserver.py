"""
MCP Server — exposes a list_doctors() tool via FastMCP (stdio transport).
doctors.json must be in the same directory as this file.

Before building:
  Copy ../../Data/doctors.json → provider_agent/agentstack_agents/doctors.json
"""
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("doctorserver")

_data_path = Path(__file__).parent / "doctors.json"
doctors: list = json.loads(_data_path.read_text())


@mcp.tool()
def list_doctors(state: str | None = None, city: str | None = None) -> list[dict]:
    """Returns doctors practicing in a specific location. Search is case-insensitive.

    Args:
        state: Two-letter state code (e.g. "CA", "TX").
        city:  City name (e.g. "Austin", "Boston").

    Returns:
        List of doctor records matching the criteria.
    """
    if not state and not city:
        return [{"error": "Please provide a state or a city."}]

    target_state = state.strip().lower() if state else None
    target_city = city.strip().lower() if city else None

    return [
        doc
        for doc in doctors
        if (not target_state or doc["address"]["state"].lower() == target_state)
        and (not target_city or doc["address"]["city"].lower() == target_city)
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")
