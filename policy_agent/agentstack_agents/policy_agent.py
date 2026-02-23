"""
Policy Agent — answers insurance coverage questions using the Anthem PDF.
Deployed on AgentStack. Requires ANTHROPIC_API_KEY env var.

Before building:
  Copy ../../Data/2026AnthemgHIPSBC.pdf → policy_agent/agentstack_agents/2026AnthemgHIPSBC.pdf
"""
import base64
import os
from pathlib import Path

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

server = Server()

_PDF_PATH = Path(__file__).parent / "2026AnthemgHIPSBC.pdf"
_pdf_data = base64.standard_b64encode(_PDF_PATH.read_bytes()).decode("utf-8")


@server.agent(name="PolicyAgent")
async def policy_agent(input: Message, context: RunContext):
    """Answers insurance policy coverage questions using the Anthem benefits PDF."""
    prompt = get_message_text(input)

    client = Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=(
            "You are an expert insurance agent. Answer coverage questions based solely on "
            "the provided policy document. Answer concisely in 2-5 lines. "
            "If the information is not in the document, say 'I don't know'."
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": _pdf_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    yield AgentMessage(text=response.content[0].text)


def run() -> None:
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
    )


if __name__ == "__main__":
    run()
