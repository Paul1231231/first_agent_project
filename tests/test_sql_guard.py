import pytest

from agent.sql_guard import UnsafeSQL, validate_sql


def test_allows_safe_select():
    sql = """
        SELECT id, name, country
        FROM customers
        LIMIT 10;
    """

    validated = validate_sql(sql)

    assert "SELECT" in validated
    assert "LIMIT 10" in validated


def test_adds_limit_to_non_aggregate_query():
    sql = """
        SELECT id, name
        FROM customers;
    """

    validated = validate_sql(sql)

    assert "LIMIT 100" in validated


def test_allows_aggregate_without_limit():
    sql = """
        SELECT COUNT(*) AS customer_count
        FROM customers;
    """

    validated = validate_sql(sql)

    assert "COUNT(*)" in validated


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO customers (name) VALUES ('Alice')",
        "UPDATE customers SET name = 'Alice'",
        "DELETE FROM customers",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN test TEXT",
        "CREATE TABLE test (id INT)",
        "TRUNCATE customers",
    ],
)
def test_rejects_write_or_ddl_sql(sql):
    with pytest.raises(UnsafeSQL):
        validate_sql(sql)


def test_rejects_multiple_statements():
    sql = """
        SELECT id FROM customers LIMIT 1;
        DELETE FROM customers;
    """

    with pytest.raises(UnsafeSQL):
        validate_sql(sql)


def test_rejects_unknown_table():
    sql = """
        SELECT id, password
        FROM users
        LIMIT 10;
    """

    with pytest.raises(UnsafeSQL):
        validate_sql(sql)


def test_rejects_sql_comments():
    sql = """
        SELECT id, name
        FROM customers
        LIMIT 10; -- dangerous comment
    """

    with pytest.raises(UnsafeSQL):
        validate_sql(sql)


def test_rejects_select_star():
    sql = """
        SELECT *
        FROM customers
        LIMIT 10;
    """

    with pytest.raises(UnsafeSQL):
        validate_sql(sql)


def test_rejects_large_limit():
    sql = """
        SELECT id, name
        FROM customers
        LIMIT 1000;
    """

    with pytest.raises(UnsafeSQL):
        validate_sql(sql)