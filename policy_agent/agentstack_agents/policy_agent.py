import base64
import os
from pathlib import Path

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from anthropic import Anthropic
from anthropic.types import (
    Base64PDFSourceParam,
    DocumentBlockParam,
    MessageParam,
    TextBlockParam,
)
from dotenv import load_dotenv

load_dotenv()

server = Server()

_PDF_PATH = Path(__file__).resolve().parent / "2026AnthemgHIPSBC.pdf"
_pdf_data = base64.standard_b64encode(_PDF_PATH.read_bytes()).decode("utf-8")


@server.agent(name="PolicyAgent")
async def policy_agent(input: Message, context: RunContext):
    """Insurance policy coverage agent — reads the Anthem 2026 PDF and answers questions."""
    prompt = get_message_text(input)

    client = Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=(
            "You are an expert insurance agent. Answer questions about insurance policies "
            "using the provided documents. Keep answers to 2-5 lines. "
            "If the information is not available, respond with 'I don't know'."
        ),
        messages=[
            MessageParam(
                role="user",
                content=[
                    DocumentBlockParam(
                        type="document",
                        source=Base64PDFSourceParam(
                            type="base64",
                            media_type="application/pdf",
                            data=_pdf_data,
                        ),
                    ),
                    TextBlockParam(type="text", text=prompt),
                ],
            )
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
