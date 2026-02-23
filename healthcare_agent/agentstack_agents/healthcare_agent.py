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

import httpx
from a2a.client import Client, ClientConfig, ClientFactory, create_text_message_object
from a2a.types import Artifact, Message, Task
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from anthropic import Anthropic

server = Server()


async def _call_agent(url: str, query: str) -> str:
    """Call an A2A sub-agent and return its text response."""
    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        client: Client = await ClientFactory.connect(
            url, client_config=ClientConfig(httpx_client=httpx_client)
        )
        message = create_text_message_object(content=query)
        async for response in client.send_message(message):
            if isinstance(response, Message):
                return get_message_text(response)
            elif isinstance(response, tuple):
                task: Task = response[0]
                if task.artifacts:
                    artifact: Artifact = task.artifacts[0]
                    return get_message_text(artifact)
    return "(no response)"


@server.agent(name="HealthcareAgent")
async def healthcare_agent(input: Message, context: RunContext):
    """
    Healthcare concierge. Delegates to PolicyAgent (insurance) and ProviderAgent
    (doctor lookup) in parallel, then combines the results into a single answer.
    """
    query = get_message_text(input)

    policy_url = os.environ.get("POLICY_AGENT_URL", "http://localhost:9999")
    provider_url = os.environ.get("PROVIDER_AGENT_URL", "http://localhost:9997")

    # Call both sub-agents concurrently
    policy_resp, provider_resp = await asyncio.gather(
        _call_agent(policy_url, query),
        _call_agent(provider_url, query),
    )

    # Combine with a lean Anthropic call
    anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
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
