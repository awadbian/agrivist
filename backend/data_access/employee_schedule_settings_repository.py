from backend.data_access.db import fetchall_dicts, get_connection

CLOSED_DAYS_TABLE = "dbo.employee_schedule_closed_days"


def create_employee_schedule_settings_tables():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
        IF OBJECT_ID('{CLOSED_DAYS_TABLE}', 'U') IS NULL
        CREATE TABLE {CLOSED_DAYS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            week_start_date DATE NOT NULL,
            date DATE NOT NULL,
            day_name NVARCHAR(30) NOT NULL,
            is_closed BIT NOT NULL DEFAULT 1,
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            CONSTRAINT UQ_employee_schedule_closed_days_week_day
                UNIQUE (week_start_date, day_name)
        )
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_closed_days_for_week(week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT week_start_date, date, day_name, is_closed
            FROM {CLOSED_DAYS_TABLE}
            WHERE week_start_date = ?
              AND is_closed = 1
            """,
            (week_start_date,),
        )
        return fetchall_dicts(cursor)
    finally:
        cursor.close()
        conn.close()


def set_closed_day(week_start_date, day_date, day_name, is_closed):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            UPDATE {CLOSED_DAYS_TABLE}
            SET date = ?,
                is_closed = ?,
                updated_at = SYSUTCDATETIME()
            WHERE week_start_date = ?
              AND day_name = ?
            """,
            (day_date, 1 if is_closed else 0, week_start_date, day_name),
        )

        if cursor.rowcount == 0:
            cursor.execute(
                f"""
                INSERT INTO {CLOSED_DAYS_TABLE}
                    (week_start_date, date, day_name, is_closed)
                VALUES (?, ?, ?, ?)
                """,
                (week_start_date, day_date, day_name, 1 if is_closed else 0),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
