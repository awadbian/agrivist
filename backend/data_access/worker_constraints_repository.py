from backend.data_access.db import fetchall_dicts, fetchone_dict, get_connection

LEGACY_EMPLOYEE_CONSTRAINTS_TABLE = "dbo.employee_constraints"
LEGACY_WORKER_CONSTRAINT_SUBMISSIONS_TABLE = "dbo.worker_constraint_submissions"
LEGACY_WORKER_CONSTRAINT_DAYS_TABLE = "dbo.worker_constraint_days"
EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE = "dbo.employee_constraint_submissions"
EMPLOYEE_CONSTRAINT_DAYS_TABLE = "dbo.employee_constraint_days"

WORK_DAYS = ("sunday", "monday", "tuesday", "wednesday", "thursday", "friday")


def create_worker_constraints_table():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
        IF OBJECT_ID('{EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}', 'U') IS NULL
        CREATE TABLE {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            employee_email NVARCHAR(255) NOT NULL,
            week_start_date DATE NOT NULL,
            notes NVARCHAR(MAX),
            submitted_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            CONSTRAINT UQ_employee_constraint_submissions_employee_week
                UNIQUE (employee_email, week_start_date)
        )
        """)

        cursor.execute(f"""
        IF OBJECT_ID('{EMPLOYEE_CONSTRAINT_DAYS_TABLE}', 'U') IS NULL
        CREATE TABLE {EMPLOYEE_CONSTRAINT_DAYS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            submission_id INT NOT NULL,
            day_of_week NVARCHAR(30) NOT NULL,
            availability NVARCHAR(30) NOT NULL,
            CONSTRAINT FK_employee_constraint_days_submissions
                FOREIGN KEY (submission_id)
                REFERENCES {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}(id),
            CONSTRAINT UQ_employee_constraint_days_submission_day
                UNIQUE (submission_id, day_of_week)
        )
        """)

        _migrate_legacy_employee_constraints(cursor)
        _migrate_legacy_worker_constraint_tables(cursor)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def _table_exists(cursor, table_name):
    cursor.execute(
        "SELECT OBJECT_ID(?, 'U') AS table_id",
        (table_name,),
    )
    row = cursor.fetchone()
    return row is not None and row[0] is not None


def _migrate_legacy_employee_constraints(cursor):
    if not _table_exists(cursor, LEGACY_EMPLOYEE_CONSTRAINTS_TABLE):
        return

    cursor.execute(f"""
    INSERT INTO {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}
        (employee_email, week_start_date, notes, submitted_at)
    SELECT
        legacy.employee_email,
        legacy.week_start_date,
        legacy.notes,
        legacy.submitted_at
    FROM {LEGACY_EMPLOYEE_CONSTRAINTS_TABLE} AS legacy
    WHERE NOT EXISTS (
        SELECT 1
        FROM {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} AS submissions
        WHERE LOWER(submissions.employee_email) = LOWER(legacy.employee_email)
          AND submissions.week_start_date = legacy.week_start_date
    )
    """)

    for day_name in WORK_DAYS:
        cursor.execute(f"""
        INSERT INTO {EMPLOYEE_CONSTRAINT_DAYS_TABLE}
            (submission_id, day_of_week, availability)
        SELECT
            submissions.id,
            ?,
            legacy.{day_name}
        FROM {LEGACY_EMPLOYEE_CONSTRAINTS_TABLE} AS legacy
        INNER JOIN {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} AS submissions
            ON LOWER(submissions.employee_email) = LOWER(legacy.employee_email)
           AND submissions.week_start_date = legacy.week_start_date
        WHERE legacy.{day_name} IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM {EMPLOYEE_CONSTRAINT_DAYS_TABLE} AS days
              WHERE days.submission_id = submissions.id
                AND days.day_of_week = ?
          )
        """, (day_name, day_name))


def _migrate_legacy_worker_constraint_tables(cursor):
    if not _table_exists(cursor, LEGACY_WORKER_CONSTRAINT_SUBMISSIONS_TABLE):
        return

    cursor.execute(f"""
    INSERT INTO {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}
        (employee_email, week_start_date, notes, submitted_at)
    SELECT
        legacy.employee_email,
        legacy.week_start_date,
        legacy.notes,
        legacy.submitted_at
    FROM {LEGACY_WORKER_CONSTRAINT_SUBMISSIONS_TABLE} AS legacy
    WHERE NOT EXISTS (
        SELECT 1
        FROM {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} AS submissions
        WHERE LOWER(submissions.employee_email) = LOWER(legacy.employee_email)
          AND submissions.week_start_date = legacy.week_start_date
    )
    """)

    if not _table_exists(cursor, LEGACY_WORKER_CONSTRAINT_DAYS_TABLE):
        return

    cursor.execute(f"""
    INSERT INTO {EMPLOYEE_CONSTRAINT_DAYS_TABLE}
        (submission_id, day_of_week, availability)
    SELECT
        submissions.id,
        legacy_days.day_of_week,
        legacy_days.availability
    FROM {LEGACY_WORKER_CONSTRAINT_DAYS_TABLE} AS legacy_days
    INNER JOIN {LEGACY_WORKER_CONSTRAINT_SUBMISSIONS_TABLE} AS legacy_submissions
        ON legacy_submissions.id = legacy_days.submission_id
    INNER JOIN {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} AS submissions
        ON LOWER(submissions.employee_email) = LOWER(legacy_submissions.employee_email)
       AND submissions.week_start_date = legacy_submissions.week_start_date
    WHERE NOT EXISTS (
        SELECT 1
        FROM {EMPLOYEE_CONSTRAINT_DAYS_TABLE} AS days
        WHERE days.submission_id = submissions.id
          AND days.day_of_week = legacy_days.day_of_week
    )
    """)


def get_worker_constraints(employee_email, week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT
                id,
                employee_email,
                week_start_date,
                notes,
                submitted_at
            FROM {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}
            WHERE LOWER(employee_email) = LOWER(?)
              AND week_start_date = ?
            """,
            (employee_email, week_start_date),
        )
        submission = fetchone_dict(cursor)
        if not submission:
            return None

        cursor.execute(
            f"""
            SELECT day_of_week, availability
            FROM {EMPLOYEE_CONSTRAINT_DAYS_TABLE}
            WHERE submission_id = ?
            """,
            (submission["id"],),
        )
        day_rows = fetchall_dicts(cursor)

        for day_name in WORK_DAYS:
            submission[day_name] = None

        for row in day_rows:
            day_name = row["day_of_week"]
            if day_name in WORK_DAYS:
                submission[day_name] = row["availability"]

        return submission
    finally:
        cursor.close()
        conn.close()


def create_worker_constraints(employee_email, week_start_date, availability, notes):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            INSERT INTO {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} (
                employee_email,
                week_start_date,
                notes
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?)
            """,
            (employee_email, week_start_date, notes),
        )
        submission_id = cursor.fetchone()[0]

        for day_name in WORK_DAYS:
            cursor.execute(
                f"""
                INSERT INTO {EMPLOYEE_CONSTRAINT_DAYS_TABLE} (
                    submission_id,
                    day_of_week,
                    availability
                )
                VALUES (?, ?, ?)
                """,
                (submission_id, day_name, availability[day_name]),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_worker_constraints(employee_email, week_start_date, availability, notes):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT id
            FROM {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}
            WHERE LOWER(employee_email) = LOWER(?)
              AND week_start_date = ?
            """,
            (employee_email, week_start_date),
        )
        existing_row = cursor.fetchone()

        if existing_row:
            submission_id = existing_row[0]
            cursor.execute(
                f"""
                UPDATE {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}
                SET notes = ?,
                    submitted_at = SYSUTCDATETIME()
                WHERE id = ?
                """,
                (notes, submission_id),
            )
            cursor.execute(
                f"""
                DELETE FROM {EMPLOYEE_CONSTRAINT_DAYS_TABLE}
                WHERE submission_id = ?
                """,
                (submission_id,),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} (
                    employee_email,
                    week_start_date,
                    notes
                )
                OUTPUT INSERTED.id
                VALUES (?, ?, ?)
                """,
                (employee_email, week_start_date, notes),
            )
            submission_id = cursor.fetchone()[0]

        for day_name in WORK_DAYS:
            cursor.execute(
                f"""
                INSERT INTO {EMPLOYEE_CONSTRAINT_DAYS_TABLE} (
                    submission_id,
                    day_of_week,
                    availability
                )
                VALUES (?, ?, ?)
                """,
                (submission_id, day_name, availability[day_name]),
            )

        conn.commit()
        return submission_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def delete_worker_constraints_for_week(week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            DELETE days
            FROM {EMPLOYEE_CONSTRAINT_DAYS_TABLE} AS days
            INNER JOIN {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} AS submissions
                ON submissions.id = days.submission_id
            WHERE submissions.week_start_date = ?
            """,
            (week_start_date,),
        )
        cursor.execute(
            f"""
            DELETE FROM {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}
            WHERE week_start_date = ?
            """,
            (week_start_date,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def delete_worker_constraints_except_week(week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            DELETE days
            FROM {EMPLOYEE_CONSTRAINT_DAYS_TABLE} AS days
            INNER JOIN {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} AS submissions
                ON submissions.id = days.submission_id
            WHERE submissions.week_start_date <> ?
            """,
            (week_start_date,),
        )
        cursor.execute(
            f"""
            DELETE FROM {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}
            WHERE week_start_date <> ?
            """,
            (week_start_date,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def delete_all_worker_constraints():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            DELETE FROM {EMPLOYEE_CONSTRAINT_DAYS_TABLE}
            """
        )
        cursor.execute(
            f"""
            DELETE FROM {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE}
            """
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_worker_constraint_submissions_for_week(week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT
                submissions.id,
                submissions.employee_email,
                submissions.week_start_date,
                submissions.notes,
                submissions.submitted_at,
                days.day_of_week,
                days.availability
            FROM {EMPLOYEE_CONSTRAINT_SUBMISSIONS_TABLE} AS submissions
            LEFT JOIN {EMPLOYEE_CONSTRAINT_DAYS_TABLE} AS days
                ON days.submission_id = submissions.id
            WHERE submissions.week_start_date = ?
            ORDER BY submissions.id, days.day_of_week
            """,
            (week_start_date,),
        )
        rows = fetchall_dicts(cursor)
        submissions_by_id = {}

        for row in rows:
            submission_id = row["id"]
            submission = submissions_by_id.get(submission_id)
            if not submission:
                submission = {
                    "id": submission_id,
                    "employee_email": row["employee_email"],
                    "week_start_date": row["week_start_date"],
                    "notes": row["notes"],
                    "submitted_at": row["submitted_at"],
                }
                for day_name in WORK_DAYS:
                    submission[day_name] = None
                submissions_by_id[submission_id] = submission

            day_name = row.get("day_of_week")
            if day_name in WORK_DAYS:
                submission[day_name] = row["availability"]

        return list(submissions_by_id.values())
    finally:
        cursor.close()
        conn.close()
