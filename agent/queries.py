from __future__ import annotations

import re
from datetime import date
from typing import Optional


MAX_LIMIT = 100


def validate_limit(limit: int) -> int:
    if not isinstance(limit, int):
        raise ValueError("limit must be an integer")

    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")

    return limit


def validate_offset(offset: int) -> int:
    if not isinstance(offset, int):
        raise ValueError("offset must be an integer")

    if offset < 0:
        raise ValueError("offset cannot be negative")

    return offset


def validate_date(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None

    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must use YYYY-MM-DD format"
        ) from exc

    return parsed.isoformat()


def validate_country(country: Optional[str]) -> Optional[str]:
    if country is None:
        return None

    country = country.strip()

    if not country:
        return None

    if len(country) > 50:
        raise ValueError("country is too long")

    # Allow normal country names only. Quotes and SQL punctuation are rejected.
    if not re.fullmatch(r"[A-Za-z][A-Za-z -]*", country):
        raise ValueError("country contains invalid characters")

    return country


def customer_count_sql() -> str:
    return """
        SELECT COUNT(*) AS customer_count
        FROM customers;
    """.strip()


def customers_sql(
    country: Optional[str],
    limit: int,
    offset: int,
) -> str:
    limit = validate_limit(limit)
    offset = validate_offset(offset)
    country = validate_country(country)

    where_clause = ""

    if country:
        # Country is strictly validated above and cannot contain quotes.
        where_clause = f"WHERE country = '{country}'"

    return f"""
        SELECT id, name, country, created_at
        FROM customers
        {where_clause}
        ORDER BY id
        LIMIT {limit}
        OFFSET {offset};
    """.strip()


def order_summary_sql(
    start_date: Optional[str],
    end_date: Optional[str],
) -> str:
    start_date = validate_date(start_date, "start_date")
    end_date = validate_date(end_date, "end_date")

    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date cannot be later than end_date")

    filters = []

    if start_date:
        filters.append(f"order_date >= DATE '{start_date}'")

    if end_date:
        filters.append(f"order_date < DATE '{end_date}' + INTERVAL '1 day'")

    where_clause = ""

    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    return f"""
        SELECT
            COUNT(*) AS order_count,
            COALESCE(SUM(total_amount), 0) AS total_revenue,
            COALESCE(AVG(total_amount), 0) AS average_order_value
        FROM orders
        {where_clause};
    """.strip()


def sales_by_product_sql(
    start_date: Optional[str],
    end_date: Optional[str],
    limit: int,
) -> str:
    start_date = validate_date(start_date, "start_date")
    end_date = validate_date(end_date, "end_date")
    limit = validate_limit(limit)

    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date cannot be later than end_date")

    filters = []

    if start_date:
        filters.append(f"o.order_date >= DATE '{start_date}'")

    if end_date:
        filters.append(f"o.order_date < DATE '{end_date}' + INTERVAL '1 day'")

    where_clause = ""

    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    return f"""
        SELECT
            p.id AS product_id,
            p.name AS product_name,
            SUM(oi.quantity) AS units_sold,
            SUM(oi.quantity * oi.unit_price) AS revenue
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        JOIN orders o ON o.id = oi.order_id
        {where_clause}
        GROUP BY p.id, p.name
        ORDER BY revenue DESC
        LIMIT {limit};
    """.strip()