from __future__ import annotations

from sqlglot import exp, parse


MAX_LIMIT = 100
ALLOWED_TABLES = {
    "customers": {"id", "name", "email", "country", "created_at"},
    "products": {"id", "name", "category", "price"},
    "orders": {"id", "customer_id", "order_date", "status", "total_amount"},
    "order_items": {"id", "order_id", "product_id", "quantity", "unit_price"},
}


class UnsafeSQL(ValueError):
    """Raised when generated SQL violates read-only safety constraints."""


def _contains_sql_comment(sql: str) -> bool:
    return "--" in sql or "/*" in sql or "*/" in sql


def _validate_single_select(statement: exp.Expression) -> exp.Select:
    if not isinstance(statement, exp.Select):
        raise UnsafeSQL("Only SELECT statements are allowed")

    return statement


def _validate_tables_and_columns(select: exp.Select) -> None:
    table_aliases: dict[str, str] = {}
    referenced_tables: set[str] = set()

    for table in select.find_all(exp.Table):
        table_name = table.name.lower()

        if table_name not in ALLOWED_TABLES:
            raise UnsafeSQL(f"Unknown or disallowed table: {table_name}")

        referenced_tables.add(table_name)
        table_aliases[table.alias_or_name.lower()] = table_name

    for column in select.find_all(exp.Column):
        if isinstance(column.this, exp.Star):
            raise UnsafeSQL("SELECT * is not allowed")

        column_name = column.name.lower()
        table_name = column.table.lower() if column.table else None

        if table_name:
            resolved_table = table_aliases.get(table_name, table_name)
            if resolved_table not in ALLOWED_TABLES:
                raise UnsafeSQL(f"Unknown or disallowed table: {resolved_table}")
            if column_name not in ALLOWED_TABLES[resolved_table]:
                raise UnsafeSQL(
                    f"Unknown or disallowed column: {resolved_table}.{column_name}"
                )
            continue

        matches = [
            table
            for table in referenced_tables
            if column_name in ALLOWED_TABLES[table]
        ]

        if not matches:
            raise UnsafeSQL(f"Unknown or disallowed column: {column_name}")

        if len(matches) > 1:
            raise UnsafeSQL(f"Ambiguous unqualified column: {column_name}")


def _contains_projection_star(select: exp.Select) -> bool:
    for projection in select.expressions:
        node = projection.this if isinstance(projection, exp.Alias) else projection

        if isinstance(node, exp.Star):
            return True

        if isinstance(node, exp.Column) and isinstance(node.this, exp.Star):
            return True

    return False


def _is_aggregate_query(select: exp.Select) -> bool:
    return (
        select.args.get("group") is not None
        or select.args.get("having") is not None
        or select.find(exp.AggFunc) is not None
    )


def _validate_or_add_limit(select: exp.Select) -> None:
    limit_expression = select.args.get("limit")

    if limit_expression is None:
        if _is_aggregate_query(select):
            return

        select.set("limit", exp.Limit(expression=exp.Literal.number(MAX_LIMIT)))
        return

    literal = limit_expression.expression

    if not isinstance(literal, exp.Literal) or not literal.is_int:
        raise UnsafeSQL("LIMIT must be a positive integer literal")

    value = int(literal.this)

    if value < 1 or value > MAX_LIMIT:
        raise UnsafeSQL(f"LIMIT must be between 1 and {MAX_LIMIT}")


def validate_sql(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise UnsafeSQL("SQL must be a non-empty string")

    if _contains_sql_comment(sql):
        raise UnsafeSQL("SQL comments are not allowed")

    try:
        statements = parse(sql, read="postgres")
    except Exception as exc:  # pragma: no cover - parser specific failures
        raise UnsafeSQL(f"Failed to parse SQL: {exc}") from exc

    statements = [statement for statement in statements if statement is not None]

    if len(statements) != 1:
        raise UnsafeSQL("Exactly one SQL statement is allowed")

    select = _validate_single_select(statements[0])

    if _contains_projection_star(select):
        raise UnsafeSQL("SELECT * is not allowed")

    _validate_tables_and_columns(select)
    _validate_or_add_limit(select)

    return select.sql(dialect="postgres")
