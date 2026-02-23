"""
Local test script for AgentStack agents.
Run each agent in a separate terminal first, then run this script.

Usage:
  python test_local.py
"""
import asyncio
import httpx
import uuid


async def query_agent(url: str, question: str) -> str:
    """Send a query to an AgentStack A2A agent via JSON-RPC."""
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": question}],
            }
        },
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{url}/jsonrpc/", json=payload)
        data = resp.json()

    result = data.get("result", {})
    for msg in reversed(result.get("history", [])):
        if msg.get("role") == "agent":
            for part in msg.get("parts", []):
                if part.get("kind") == "text":
                    return part["text"]
    return "(no response)"


async def main():
    agents = {
        "ResearchAgent":  "http://127.0.0.1:8001",
        "PolicyAgent":    "http://127.0.0.1:8002",
        "ProviderAgent":  "http://127.0.0.1:8003",
        "HealthcareAgent":"http://127.0.0.1:8004",
    }
    questions = {
        "ResearchAgent":   "What are common symptoms of anxiety disorder?",
        "PolicyAgent":     "How much would I pay for mental health therapy?",
        "ProviderAgent":   "Are there any Psychiatrists near me in Austin, TX?",
        "HealthcareAgent": "I'm in Austin, TX. How do I get mental health therapy and what does my insurance cover?",
    }

    for name, url in agents.items():
        try:
            card = httpx.get(f"{url}/.well-known/agent-card.json", timeout=5).json()
            q = questions[name]
            print(f"\n{'='*60}")
            print(f"Agent : {card['name']}")
            print(f"Q: {q}")
            answer = await query_agent(url, q)
            print(f"A: {answer}")
        except Exception as e:
            print(f"\n[{name}] Not reachable at {url}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
