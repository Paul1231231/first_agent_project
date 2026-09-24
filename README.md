# AI Database Agent POC

A proof-of-concept AI database agent that uses **LangChain + Ollama + MCP + PostgreSQL**.

The LLM decides whether to call approved application tools (pre-written SQL) or produce SQL directly. Directly generated SQL is validated by `first_agent_project.sql_guard.validate_sql` before execution through the PostgreSQL MCP server.

## Architecture

User → LangChain/Ollama agent → approved tools or validated generated SQL → MCP `query` tool → PostgreSQL

## Project structure

```text
first_agent_project/
├── database/
│   ├── schema.sql
│   └── synthetic.sql
├── src/
│   └── first_agent_project/
│       ├── __init__.py
│       ├── __main__.py
│       ├── agent.py
│       ├── prompts.py
│       ├── queries.py
│       ├── sql_extraction.py
│       ├── sql_guard.py
│       └── tools.py
├── tests/
│   ├── fakes.py
│   ├── test_package_entrypoint.py
│   ├── test_queries.py
│   ├── test_sql_extraction.py
│   ├── test_sql_guard.py
│   └── test_tools.py
├── .env.example
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## Requirements

- Python (as specified in `pyproject.toml`)
- PostgreSQL
- Ollama running locally with a compatible model (default code uses `llama3.2:3b`)
- Node.js / `npx` (to run `@modelcontextprotocol/server-postgres`)

## Environment variables

Copy `.env.example` to `.env` and fill in your local values:

```bash
cp .env.example .env
```

Required:

- `DATABASE_URL` - PostgreSQL connection URL used by the MCP PostgreSQL server

## Install

### With uv

```bash
uv sync
```

### With pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run tests

```bash
pytest
```

## Run the agent

Any of the following entry points are supported:

```bash
first-agent-project
python -m first_agent_project
python -c "from first_agent_project import main; main()"
```
