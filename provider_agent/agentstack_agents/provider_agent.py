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

_MCP_SERVER_PATH = str(Path(__file__).resolve().parent / "mcpserver.py")


@server.agent(name="ProviderAgent")
async def provider_agent(input: Message, context: RunContext):
    """Healthcare provider agent — finds doctors by location and specialty via MCP tool."""
    prompt = get_message_text(input)

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

    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
    agent = create_agent(
        llm,
        tools,
        name="HealthcareProviderAgent",
        system_prompt=(
            "Your task is to find and list providers using the find_healthcare_providers "
            "MCP Tool based on the user's query. Only use providers based on the response "
            "from the tool. Output the information in a table."
        ),
    )

    response = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    yield AgentMessage(text=response["messages"][-1].content)


def run() -> None:
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
    )


if __name__ == "__main__":
    run()
