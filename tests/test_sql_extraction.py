from first_agent_project.sql_extraction import extract_generated_sql


def test_extracts_sql_from_expected_fenced_block():
    content = """
    Reasoning: ...
    SQL:
    ```sql
    SELECT id, name
    FROM customers
    LIMIT 10;
    ```
    """

    assert extract_generated_sql(content) == "SELECT id, name\n    FROM customers\n    LIMIT 10;"


def test_returns_none_when_sql_block_missing():
    content = "No SQL was generated for this response."

    assert extract_generated_sql(content) is None


def test_returns_none_for_empty_sql_block():
    content = """
    SQL:
    ```sql
    ```
    """

    assert extract_generated_sql(content) is None