import argparse

from backend.data_access.db import get_connection


def list_tables(cursor):
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)

    return cursor.fetchall()


def print_connection_info(cursor):
    cursor.execute("SELECT DB_NAME()")
    database_name = cursor.fetchone()[0]
    print("Connected successfully!")
    print(f"Current database: {database_name}")

    rows = list_tables(cursor)
    if rows:
        print("Existing tables:")
        for row in rows:
            print(f"- {row.TABLE_SCHEMA}.{row.TABLE_NAME}")
    else:
        print("No tables found.")


def main():
    parser = argparse.ArgumentParser(description="Test Azure SQL connection.")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create or update the required database tables before listing tables.",
    )
    args = parser.parse_args()

    if args.init:
        from backend.data_access.init_db import create_tables

        create_tables()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print_connection_info(cursor)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
