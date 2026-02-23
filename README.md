# Healthcare Multi-Agent System — AgentStack Deployment

Four agents deployed on the AgentStack platform using BeeAI framework and A2A protocol.

## Overview

This system demonstrates a multi-agent healthcare concierge built on AgentStack:

1. **HealthcareAgent** — Orchestrator using BeeAI `RequirementAgent` + `HandoffTool`. Routes questions to sub-agents discovered automatically on the platform.
2. **PolicyAgent** — Reads the Anthem 2026 benefits PDF and answers insurance coverage questions using the platform LLM.
3. **ProviderAgent** — Finds in-network doctors by city/state via LangChain + MCP tool backed by a JSON provider database.
4. **ResearchAgent** — Searches the web via Serper API (Google search) to answer health condition and treatment questions.

## Folder Structure

```
agentstack-healthcare/
├── policy_agent/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   └── agentstack_agents/
│       ├── __init__.py
│       ├── policy_agent.py
│       └── 2026AnthemgHIPSBC.pdf
├── research_agent/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   └── agentstack_agents/
│       ├── __init__.py
│       ├── research_agent.py
│       └── streaming_citation_parser.py
├── provider_agent/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   └── agentstack_agents/
│       ├── __init__.py
│       ├── provider_agent.py
│       ├── mcpserver.py
│       └── doctors.json
└── healthcare_agent/
    ├── Dockerfile
    ├── pyproject.toml
    ├── uv.lock
    └── agentstack_agents/
        ├── __init__.py
        └── healthcare_agent.py
```

## Setup

### 1. Deploy to AgentStack using the CLI

Install the AgentStack CLI and add each agent from your repository:

```bash
agentstack add https://github.com/Tamilselvan1915/agentstack-deployment@main#path=/policy_agent
agentstack add https://github.com/Tamilselvan1915/agentstack-deployment@main#path=/research_agent
agentstack add https://github.com/Tamilselvan1915/agentstack-deployment@main#path=/provider_agent
agentstack add https://github.com/Tamilselvan1915/agentstack-deployment@main#path=/healthcare_agent
```

### 2. Configure LLM extensions

Each agent uses the AgentStack **LLM Service Extension** — no API keys hardcoded in the agent. Configure a Gemini (or other) LLM key on the AgentStack platform for each agent.

Suggested model: `gemini:gemini-2.5-flash-lite`

### 3. Configure environment variables

| Agent          | Variable        | Description                      |
|----------------|-----------------|----------------------------------|
| ResearchAgent  | SERPER_API_KEY  | Serper API key for Google search |

Get a free Serper API key at [serper.dev](https://serper.dev).

All other credentials are provided via the AgentStack LLM extension — no `ANTHROPIC_API_KEY` needed.

### 4. Deploy order

Deploy **PolicyAgent**, **ResearchAgent**, and **ProviderAgent** first.
Then deploy **HealthcareAgent** — it auto-discovers the others via `AgentStackAgent.from_agent_stack()`.

## Sample Queries

**HealthcareAgent:**
> "I need mental health assistance in Austin, Texas — who can I see and what's covered?"

**PolicyAgent:**
> "What is my coinsurance for office visits in-network versus out-of-network?"

**ProviderAgent:**
> "What dermatologists practice in Los Angeles?"

**ResearchAgent:**
> "What are the symptoms and treatment options for Type 2 diabetes?"

## Architecture

The **HealthcareAgent** uses BeeAI's `RequirementAgent` with `HandoffTool` to delegate questions to specialized agents discovered on the AgentStack platform. It enforces that all three sub-agents are consulted before returning a final answer.

The LLM for all agents is provided dynamically by the AgentStack platform — no vendor lock-in.
