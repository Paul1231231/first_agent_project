AI Database Agent POC

A proof-of-concept AI database agent that uses LangChain + Ollama + MCP + PostgreSQL.

The LLM decides which application-level tool to call. Each application tool contains a pre-written SQL query and uses the live MCP session to execute that SQL through the PostgreSQL MCP server.

Architecture

                         User
                           |
                           v
                  +------------------+
                  |  LangChain / LLM |
                  |    (Ollama)      |
                  +--------+---------+
                           |
                           | chooses tool
                           v
              +--------------------------+
              | LangChain application    |
              | tools                    |
              |                          |
              | get_customer_emails()    |
              | get_customer_names()     |
              | ...                      |
              +------------+-------------+
                           |
                           | pre-written SQL
                           v
              +--------------------------+
              | MCP ClientSession        |
              +------------+-------------+
                           |
                           | call_tool("query", ...)
                           v
              +--------------------------+
              | PostgreSQL MCP Server    |
              | @modelcontextprotocol/  |
              | server-postgres          |
              +------------+-------------+
                           |
                           v
                    +------------+
                    | PostgreSQL  |
                    +------------+


```text
first_agent_project/
├── agent/
│   ├── agent.py
│   ├── prompts.py
│   ├── queries.py
│   ├── sql_guard.py
│   └── tools.py
├── database/
│   ├── schema.sql
│   └── synthetic.sql
├── mcp_server/
│   └── database.py
└── README.md
```
