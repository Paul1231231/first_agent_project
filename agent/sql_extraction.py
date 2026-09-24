from __future__ import annotations

import re


SQL_PATTERN = re.compile(
    r"SQL:\s*```sql\s*(.*?)```",
    re.IGNORECASE | re.DOTALL,
)


def extract_generated_sql(content: str) -> str | None:
    """Extract SQL from the required model response format."""

    match = SQL_PATTERN.search(content)

    if not match:
        return None

    sql = match.group(1).strip()

    if not sql:
        return None

    return sql