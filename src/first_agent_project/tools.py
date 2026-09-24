from __future__ import annotations

import json
from typing import Any, Optional

from langchain_core.tools import tool

from .queries import (
    customer_count_sql,
    customers_sql,
    order_summary_sql,
    sales_by_product_sql,
)


def extract_result(result: Any) -> str:
    """Extract text content from an MCP result."""
    if not result or not getattr(result, "content", None):
        return ""

    parts: list[str] = []

    for item in result.content:
        text = getattr(item, "text", None)

        if text:
            parts.append(text)

    return "\n".join(parts)


def structured_result(result: Any) -> str:
    """Return MCP output as bounded JSON when possible."""
    text = extract_result(result)

    if not text:
        return json.dumps({"rows": [], "message": "No results found"})

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return json.dumps({"result": text})

    return json.dumps(parsed, default=str)


async def execute_query(session: Any, sql: str) -> str:
    """Execute one approved read-only query through MCP."""
    try:
        result = await session.call_tool(
            name="query",
            arguments={"sql": sql},
        )
    except Exception as exc:
        raise RuntimeError(f"Database query failed: {exc}") from exc

    return structured_result(result)


def create_tools(session: Any):
    """Create the approved LangChain database tools."""

    @tool
    async def get_customer_count() -> str:
        """Return the total number of customers."""
        return await execute_query(session, customer_count_sql())

    @tool
    async def list_customers(
        country: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        """List customers, optionally filtered by country."""
        sql = customers_sql(
            country=country,
            limit=limit,
            offset=offset,
        )
        return await execute_query(session, sql)

    @tool
    async def get_order_summary(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Return order count, revenue, and average order value."""
        sql = order_summary_sql(
            start_date=start_date,
            end_date=end_date,
        )
        return await execute_query(session, sql)

    @tool
    async def get_sales_by_product(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """Return product sales totals, optionally filtered by date."""
        sql = sales_by_product_sql(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return await execute_query(session, sql)

    return [
        get_customer_count,
        list_customers,
        get_order_summary,
        get_sales_by_product,
    ]