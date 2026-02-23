import asyncio
import os
import uuid

import httpx
from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

server = Server()


async def _call_agent(url: str, query: str) -> str:
    """Call a deployed AgentStack A2A agent via JSON-RPC and return its text response."""
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": query}],
            }
        },
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{url.rstrip('/')}/jsonrpc/", json=payload)
        resp.raise_for_status()
        data = resp.json()

    result = data.get("result", {})
    # AgentStack history format
    for msg in reversed(result.get("history", [])):
        if msg.get("role") == "agent":
            for part in msg.get("parts", []):
                if part.get("kind") == "text":
                    return part["text"]
    # Fallback: artifacts format (standard A2A)
    for artifact in result.get("artifacts", []):
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                return part["text"]
    return "(no response)"


@server.agent(name="HealthcareAgent")
async def healthcare_agent(input: Message, context: RunContext):
    """
    Healthcare concierge orchestrator — calls PolicyAgent and ProviderAgent in parallel,
    then uses Claude to summarize both responses into a single answer.

    Required env vars (set on AgentStack platform):
      ANTHROPIC_API_KEY   — Anthropic API key
      POLICY_AGENT_URL    — Deployed URL of PolicyAgent
      PROVIDER_AGENT_URL  — Deployed URL of ProviderAgent
    """
    query = get_message_text(input)

    policy_url = os.environ.get("POLICY_AGENT_URL", "http://localhost:8001")
    provider_url = os.environ.get("PROVIDER_AGENT_URL", "http://localhost:8002")

    # Call both sub-agents in parallel
    policy_resp, provider_resp = await asyncio.gather(
        _call_agent(policy_url, query),
        _call_agent(provider_url, query),
    )

    # Combine with a direct Anthropic call
    anthropic = Anthropic()
    result = anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system="Summarize responses from sub-agents into a clear answer. Cite each agent by name.",
        messages=[
            {
                "role": "user",
                "content": (
                    f"User question: {query}\n\n"
                    f"PolicyAgent: {policy_resp}\n\n"
                    f"ProviderAgent: {provider_resp}"
                ),
            }
        ],
    )

    yield AgentMessage(text=result.content[0].text)


def run() -> None:
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
    )


if __name__ == "__main__":
    run()
