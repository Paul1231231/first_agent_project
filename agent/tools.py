from langchain_core.tools import tool

from queries import EMAIL_SQL, NAME_SQL

def create_tools(session):
    @tool
    async def get_customer_emails() -> str:
        """Get email of all customers."""
        result = await session.call_tool(
            "query",
            {"sql": EMAIL_SQL},
        )

        return extract_result(result)

    @tool
    async def get_customer_names() -> str:
        """Fetches all customer names from the database."""
        result = await session.call_tool(
            "query",
            {"sql": NAME_SQL},
        )

        return extract_result(result)

    return [get_customer_emails, get_customer_names]

def extract_result(result) -> str:
    parts = []
    for item in result.content:
        if hasattr(item, "text"):
            parts.append(item.text)

    return "\n".join(parts)