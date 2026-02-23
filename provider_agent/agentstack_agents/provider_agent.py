"""
Provider Agent — finds healthcare providers by location using LangChain + MCP.
Deployed on AgentStack. Requires ANTHROPIC_API_KEY env var.

Before building:
  Copy ../../Data/doctors.json → provider_agent/agentstack_agents/doctors.json
"""
import os
import sys
from pathlib import Path

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

load_dotenv()

server = Server()

_MCP_SERVER_PATH = str(Path(__file__).parent / "mcpserver.py")


@server.agent(name="ProviderAgent")
async def provider_agent(input: Message, context: RunContext):
    """Finds healthcare providers near the user's location using a doctor database."""
    prompt = get_message_text(input)

    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

    mcp_client = MultiServerMCPClient(
        {
            "find_healthcare_providers": StdioConnection(
                transport="stdio",
                command=sys.executable,
                args=[_MCP_SERVER_PATH],
            )
        }
    )

    tools = await mcp_client.get_tools()
    agent = create_agent(
        llm,
        tools,
        name="HealthcareProviderAgent",
        system_prompt=(
            "Find and list providers using the available MCP tool(s). "
            "Call the tool to retrieve providers and ground your response strictly on its output."
        ),
    )

    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]}
    )
    yield AgentMessage(text=response["messages"][-1].content)


def run() -> None:
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
    )


if __name__ == "__main__":
    run()
