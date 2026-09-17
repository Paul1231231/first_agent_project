BLOCKED_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE"
]


def validate_sql(sql: str):

    normalized = sql.upper()

    for keyword in BLOCKED_KEYWORDS:
        if keyword in normalized:
            raise ValueError(
                f"Unsafe SQL operation: {keyword}"
            )

    return True