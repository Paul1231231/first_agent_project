import json

import pytest

from first_agent_project.tools import create_tools, extract_result
from tests.fakes import FakeContent, FakeMCPResult, FakeMCPSession


def test_extract_result_reads_text_content():
    result = FakeMCPResult(
        content=[
            FakeContent(text='{"rows": [{"name": "Alice"}]}'),
        ]
    )

    assert extract_result(result) == '{"rows": [{"name": "Alice"}]}'


def test_extract_result_handles_empty_content():
    result = FakeMCPResult(content=[])

    assert extract_result(result) == ""


@pytest.mark.asyncio
async def test_get_customer_count_calls_expected_query():
    session = FakeMCPSession(
        response_text='{"rows": [{"customer_count": 100}]}'
    )

    tools = create_tools(session)
    tool = next(tool for tool in tools if tool.name == "get_customer_count")

    result = await tool.ainvoke({})

    assert json.loads(result) == {
        "rows": [{"customer_count": 100}]
    }

    assert len(session.calls) == 1
    assert session.calls[0]["name"] == "query"
    assert "COUNT(*)" in session.calls[0]["arguments"]["sql"]


@pytest.mark.asyncio
async def test_list_customers_passes_country_and_limit():
    session = FakeMCPSession(
        response_text='{"rows": [{"id": 1, "name": "Alice"}]}'
    )

    tools = create_tools(session)
    tool = next(tool for tool in tools if tool.name == "list_customers")

    await tool.ainvoke(
        {
            "country": "Japan",
            "limit": 5,
            "offset": 10,
        }
    )

    sql = session.calls[0]["arguments"]["sql"]

    assert "country = 'Japan'" in sql
    assert "LIMIT 5" in sql
    assert "OFFSET 10" in sql


@pytest.mark.asyncio
async def test_order_summary_uses_date_filters():
    session = FakeMCPSession()

    tools = create_tools(session)
    tool = next(tool for tool in tools if tool.name == "get_order_summary")

    await tool.ainvoke(
        {
            "start_date": "2026-01-01",
            "end_date": "2026-09-23",
        }
    )

    sql = session.calls[0]["arguments"]["sql"]

    assert "2026-01-01" in sql
    assert "2026-09-23" in sql
    assert "FROM orders" in sql


@pytest.mark.asyncio
async def test_sales_by_product_is_bounded():
    session = FakeMCPSession()

    tools = create_tools(session)
    tool = next(tool for tool in tools if tool.name == "get_sales_by_product")

    await tool.ainvoke({"limit": 10})

    sql = session.calls[0]["arguments"]["sql"]

    assert "LIMIT 10" in sql
    assert "FROM order_items" in sql


@pytest.mark.asyncio
async def test_mcp_error_is_reported():
    session = FakeMCPSession(
        error=RuntimeError("database unavailable")
    )

    tools = create_tools(session)
    tool = next(tool for tool in tools if tool.name == "get_customer_count")

    with pytest.raises(RuntimeError, match="Database query failed"):
        await tool.ainvoke({})