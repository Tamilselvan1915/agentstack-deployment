import os

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from anthropic import Anthropic
from anthropic.types import MessageParam
from dotenv import load_dotenv

load_dotenv()

server = Server()


@server.agent(name="ResearchAgent")
async def research_agent(input: Message, context: RunContext):
    """Healthcare research agent — answers questions about conditions, symptoms, and treatments."""
    prompt = get_message_text(input)

    client = Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=(
            "You are a healthcare research agent. Provide information about "
            "health conditions, symptoms, treatments, and procedures. "
            "Keep answers to 2-5 lines. If you don't know, say so."
        ),
        messages=[MessageParam(role="user", content=prompt)],
    )

    yield AgentMessage(text=response.content[0].text)


def run() -> None:
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
    )


if __name__ == "__main__":
    run()
