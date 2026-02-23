"""
Healthcare Orchestrator — calls PolicyAgent and ProviderAgent in parallel via A2A,
then uses Claude to combine and summarize the results.

Deployed on AgentStack. Required env vars:
  ANTHROPIC_API_KEY  — Anthropic API key
  POLICY_AGENT_URL   — URL of the deployed PolicyAgent  (e.g. https://policy-agent.agentstack.run)
  PROVIDER_AGENT_URL — URL of the deployed ProviderAgent (e.g. https://provider-agent.agentstack.run)
"""
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
    """Call an A2A sub-agent via JSON-RPC and return its text response."""
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
    # Fallback: artifacts format
    for artifact in result.get("artifacts", []):
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                return part["text"]
    return "(no response)"


@server.agent(name="HealthcareAgent")
async def healthcare_agent(input: Message, context: RunContext):
    """
    Healthcare concierge. Delegates to PolicyAgent (insurance) and ProviderAgent
    (doctor lookup) in parallel, then combines the results into a single answer.
    """
    query = get_message_text(input)

    policy_url = os.environ.get("POLICY_AGENT_URL", "http://localhost:8001")
    provider_url = os.environ.get("PROVIDER_AGENT_URL", "http://localhost:8002")

    # Call both sub-agents concurrently
    policy_resp, provider_resp = await asyncio.gather(
        _call_agent(policy_url, query),
        _call_agent(provider_url, query),
    )

    # Combine with a lean Anthropic call
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
