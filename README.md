# Healthcare Multi-Agent System — AgentStack Deployment

Four agents packaged for the AgentStack platform, following the A2A protocol.

## Folder Structure

```
agentstack-healthcare/
├── policy_agent/          # Insurance coverage Q&A (reads Anthem PDF)
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── agentstack_agents/
│       ├── __init__.py
│       └── policy_agent.py
│       └── 2026AnthemgHIPSBC.pdf  ← copy here (see step 1)
├── research_agent/        # Healthcare Q&A using Claude
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── agentstack_agents/
│       ├── __init__.py
│       └── research_agent.py
├── provider_agent/        # Find doctors via LangChain + MCP
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── agentstack_agents/
│       ├── __init__.py
│       ├── provider_agent.py
│       ├── mcpserver.py
│       └── doctors.json   ← copy here (see step 1)
└── healthcare_agent/      # Orchestrator (calls policy + provider in parallel)
    ├── Dockerfile
    ├── pyproject.toml
    └── agentstack_agents/
        ├── __init__.py
        └── healthcare_agent.py
```

## Setup Steps

### 1. Copy data files

```
copy ..\Data\2026AnthemgHIPSBC.pdf  policy_agent\agentstack_agents\
copy ..\Data\doctors.json            provider_agent\agentstack_agents\
```

### 2. Generate uv lock files (requires [uv](https://docs.astral.sh/uv/))

Run in each agent folder before building Docker images:

```
cd policy_agent   && uv lock && cd ..
cd research_agent && uv lock && cd ..
cd provider_agent && uv lock && cd ..
cd healthcare_agent && uv lock && cd ..
```

### 3. Build Docker images

```
docker build -t policy-agent    ./policy_agent
docker build -t research-agent  ./research_agent
docker build -t provider-agent  ./provider_agent
docker build -t healthcare-agent ./healthcare_agent
```

### 4. Deploy on AgentStack

Push each image to your container registry and deploy as separate agents.

#### Required environment variables per agent

| Agent             | Env Var              | Value                          |
|-------------------|----------------------|--------------------------------|
| policy_agent      | ANTHROPIC_API_KEY    | your Anthropic API key         |
| research_agent    | ANTHROPIC_API_KEY    | your Anthropic API key         |
| provider_agent    | ANTHROPIC_API_KEY    | your Anthropic API key         |
| healthcare_agent  | ANTHROPIC_API_KEY    | your Anthropic API key         |
| healthcare_agent  | POLICY_AGENT_URL     | deployed URL of PolicyAgent    |
| healthcare_agent  | PROVIDER_AGENT_URL   | deployed URL of ProviderAgent  |

### 5. Agent names on AgentStack platform

| Agent             | Name registered       |
|-------------------|-----------------------|
| policy_agent      | PolicyAgent           |
| research_agent    | ResearchAgent         |
| provider_agent    | ProviderAgent         |
| healthcare_agent  | HealthcareAgent       |

Deploy order: policy, research, provider first — then healthcare (needs their URLs).
