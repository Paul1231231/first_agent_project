import pytest

from agent.queries import (
    customers_sql,
    order_summary_sql,
    sales_by_product_sql,
    validate_date,
    validate_limit,
    validate_offset,
)


def test_limit_must_be_bounded():
    with pytest.raises(ValueError):
        validate_limit(0)

    with pytest.raises(ValueError):
        validate_limit(101)


def test_offset_cannot_be_negative():
    with pytest.raises(ValueError):
        validate_offset(-1)


def test_date_must_use_iso_format():
    assert validate_date("2026-09-23", "start_date") == "2026-09-23"

    with pytest.raises(ValueError):
        validate_date("23/09/2026", "start_date")


def test_start_date_cannot_be_after_end_date():
    with pytest.raises(ValueError):
        order_summary_sql(
            start_date="2026-09-24",
            end_date="2026-09-23",
        )


def test_country_rejects_sql_injection_characters():
    with pytest.raises(ValueError):
        customers_sql(
            country="Japan' OR 1=1 --",
            limit=10,
            offset=0,
        )


def test_customer_query_contains_limit_and_offset():
    sql = customers_sql(
        country="Japan",
        limit=10,
        offset=20,
    )

    assert "LIMIT 10" in sql
    assert "OFFSET 20" in sql
    assert "country = 'Japan'" in sql


def test_order_summary_without_dates():
    sql = order_summary_sql(None, None)

    assert "FROM orders" in sql
    assert "WHERE" not in sql


def test_order_summary_with_dates():
    sql = order_summary_sql(
        start_date="2026-01-01",
        end_date="2026-09-23",
    )

    assert "2026-01-01" in sql
    assert "2026-09-23" in sql


def test_sales_by_product_contains_limit():
    sql = sales_by_product_sql(
        start_date=None,
        end_date=None,
        limit=15,
    )

    assert "GROUP BY p.id, p.name" in sql
    assert "LIMIT 15" in sql