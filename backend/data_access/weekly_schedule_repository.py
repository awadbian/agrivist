from backend.data_access.db import fetchall_dicts, fetchone_dict, get_connection
from datetime import timedelta

WEEKLY_SCHEDULE_WEEKS_TABLE = "dbo.weekly_schedule_weeks"
WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE = "dbo.weekly_schedule_assignments"
SCHEDULE_STATUS_DRAFT = "draft"
SCHEDULE_STATUS_PUBLISHED = "published"
CONSTRAINTS_STATUS_OPEN = "open"
CONSTRAINTS_STATUS_CLOSED = "closed"


def _week_end_date(week_start_date):
    return week_start_date + timedelta(days=5)


def create_weekly_schedule_tables():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
        IF OBJECT_ID('{WEEKLY_SCHEDULE_WEEKS_TABLE}', 'U') IS NULL
        CREATE TABLE {WEEKLY_SCHEDULE_WEEKS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            week_start_date DATE NOT NULL UNIQUE,
            week_end_date DATE NULL,
            status NVARCHAR(30) NOT NULL DEFAULT 'draft',
            schedule_status NVARCHAR(30) NOT NULL DEFAULT 'draft',
            constraints_status NVARCHAR(30) NOT NULL DEFAULT 'closed',
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            published_at DATETIME2 NULL
        )
        """)
        cursor.execute(f"""
        IF COL_LENGTH('{WEEKLY_SCHEDULE_WEEKS_TABLE}', 'week_end_date') IS NULL
        ALTER TABLE {WEEKLY_SCHEDULE_WEEKS_TABLE}
        ADD week_end_date DATE NULL
        """)
        cursor.execute(f"""
        IF COL_LENGTH('{WEEKLY_SCHEDULE_WEEKS_TABLE}', 'schedule_status') IS NULL
        ALTER TABLE {WEEKLY_SCHEDULE_WEEKS_TABLE}
        ADD schedule_status NVARCHAR(30) NOT NULL
            CONSTRAINT DF_weekly_schedule_weeks_schedule_status DEFAULT 'draft'
        """)
        cursor.execute(f"""
        IF COL_LENGTH('{WEEKLY_SCHEDULE_WEEKS_TABLE}', 'constraints_status') IS NULL
        ALTER TABLE {WEEKLY_SCHEDULE_WEEKS_TABLE}
        ADD constraints_status NVARCHAR(30) NOT NULL
            CONSTRAINT DF_weekly_schedule_weeks_constraints_status DEFAULT 'closed'
        """)
        cursor.execute(f"""
        UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
        SET week_end_date = DATEADD(day, 5, week_start_date)
        WHERE week_end_date IS NULL
        """)
        cursor.execute(f"""
        UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
        SET schedule_status = status
        WHERE schedule_status IS NULL
           OR schedule_status NOT IN ('draft', 'published')
        """)

        cursor.execute(f"""
        IF OBJECT_ID('{WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE}', 'U') IS NULL
        CREATE TABLE {WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            weekly_schedule_id INT NOT NULL,
            employee_email NVARCHAR(255) NOT NULL,
            employee_name NVARCHAR(255) NULL,
            work_date DATE NOT NULL,
            day_name NVARCHAR(30) NOT NULL,
            shift_type NVARCHAR(30) NOT NULL,
            start_time NVARCHAR(5) NULL,
            end_time NVARCHAR(5) NULL,
            notes NVARCHAR(MAX) NULL,
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            CONSTRAINT FK_weekly_schedule_assignments_week
                FOREIGN KEY (weekly_schedule_id)
                REFERENCES {WEEKLY_SCHEDULE_WEEKS_TABLE}(id)
                ON DELETE CASCADE
        )
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_weekly_schedule_week(week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT
                id,
                week_start_date,
                COALESCE(week_end_date, DATEADD(day, 5, week_start_date)) AS week_end_date,
                COALESCE(schedule_status, status) AS status,
                COALESCE(schedule_status, status) AS schedule_status,
                constraints_status,
                created_at,
                updated_at,
                published_at
            FROM {WEEKLY_SCHEDULE_WEEKS_TABLE}
            WHERE week_start_date = ?
            """,
            (week_start_date,),
        )
        return fetchone_dict(cursor)
    finally:
        cursor.close()
        conn.close()


def get_weekly_schedule_assignments(week_start_date, status=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        params = (week_start_date, status) if status else (week_start_date,)
        cursor.execute(
            f"""
            SELECT
                weeks.week_start_date,
                COALESCE(weeks.week_end_date, DATEADD(day, 5, weeks.week_start_date)) AS week_end_date,
                COALESCE(weeks.schedule_status, weeks.status) AS status,
                COALESCE(weeks.schedule_status, weeks.status) AS schedule_status,
                weeks.constraints_status,
                assignments.employee_email,
                assignments.employee_name,
                assignments.work_date,
                assignments.day_name,
                assignments.shift_type,
                assignments.start_time,
                assignments.end_time,
                assignments.notes
            FROM {WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE} AS assignments
            INNER JOIN {WEEKLY_SCHEDULE_WEEKS_TABLE} AS weeks
                ON weeks.id = assignments.weekly_schedule_id
            WHERE weeks.week_start_date = ?
              {"AND COALESCE(weeks.schedule_status, weeks.status) = ?" if status else ""}
            ORDER BY assignments.work_date, assignments.start_time, assignments.employee_name
            """,
            params,
        )
        return fetchall_dicts(cursor)
    finally:
        cursor.close()
        conn.close()


def get_published_assignments_for_employee(employee_email, week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT
                weeks.week_start_date,
                assignments.employee_email,
                assignments.employee_name,
                assignments.work_date,
                assignments.day_name,
                assignments.shift_type,
                assignments.start_time,
                assignments.end_time,
                assignments.notes
            FROM {WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE} AS assignments
            INNER JOIN {WEEKLY_SCHEDULE_WEEKS_TABLE} AS weeks
                ON weeks.id = assignments.weekly_schedule_id
            WHERE LOWER(assignments.employee_email) = LOWER(?)
              AND weeks.week_start_date = ?
              AND COALESCE(weeks.schedule_status, weeks.status) = 'published'
            ORDER BY assignments.work_date, assignments.start_time
            """,
            (employee_email, week_start_date),
        )
        return fetchall_dicts(cursor)
    finally:
        cursor.close()
        conn.close()


def get_published_assignments_for_employee_between(employee_email, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT
                weeks.week_start_date,
                COALESCE(weeks.week_end_date, DATEADD(day, 5, weeks.week_start_date)) AS week_end_date,
                assignments.employee_email,
                assignments.employee_name,
                assignments.work_date,
                assignments.day_name,
                assignments.shift_type,
                assignments.start_time,
                assignments.end_time,
                assignments.notes
            FROM {WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE} AS assignments
            INNER JOIN {WEEKLY_SCHEDULE_WEEKS_TABLE} AS weeks
                ON weeks.id = assignments.weekly_schedule_id
            WHERE LOWER(assignments.employee_email) = LOWER(?)
              AND assignments.work_date BETWEEN ? AND ?
              AND COALESCE(weeks.schedule_status, weeks.status) = 'published'
            ORDER BY assignments.work_date, assignments.start_time
            """,
            (employee_email, start_date, end_date),
        )
        return fetchall_dicts(cursor)
    finally:
        cursor.close()
        conn.close()


def get_published_assignments_for_week(week_start_date):
    return get_weekly_schedule_assignments(week_start_date, status="published")


def get_active_published_week():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT TOP 1
                id,
                week_start_date,
                COALESCE(week_end_date, DATEADD(day, 5, week_start_date)) AS week_end_date,
                COALESCE(schedule_status, status) AS status,
                COALESCE(schedule_status, status) AS schedule_status,
                constraints_status,
                created_at,
                updated_at,
                published_at
            FROM {WEEKLY_SCHEDULE_WEEKS_TABLE}
            WHERE COALESCE(schedule_status, status) = 'published'
            ORDER BY published_at DESC, updated_at DESC, id DESC
            """,
        )
        return fetchone_dict(cursor)
    finally:
        cursor.close()
        conn.close()


def get_active_published_assignments():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT
                weeks.week_start_date,
                weeks.status,
                assignments.employee_email,
                assignments.employee_name,
                assignments.work_date,
                assignments.day_name,
                assignments.shift_type,
                assignments.start_time,
                assignments.end_time,
                assignments.notes
            FROM {WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE} AS assignments
            INNER JOIN {WEEKLY_SCHEDULE_WEEKS_TABLE} AS weeks
                ON weeks.id = assignments.weekly_schedule_id
            WHERE weeks.id = (
                SELECT TOP 1 id
                FROM {WEEKLY_SCHEDULE_WEEKS_TABLE}
                WHERE COALESCE(schedule_status, status) = 'published'
                ORDER BY published_at DESC, updated_at DESC, id DESC
            )
            ORDER BY assignments.work_date, assignments.start_time, assignments.employee_name
            """,
        )
        return fetchall_dicts(cursor)
    finally:
        cursor.close()
        conn.close()


def save_weekly_schedule_draft(week_start_date, assignments, publish=False):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        target_status = SCHEDULE_STATUS_PUBLISHED if publish else SCHEDULE_STATUS_DRAFT
        cursor.execute(
            f"""
            SELECT id, COALESCE(schedule_status, status) AS status
            FROM {WEEKLY_SCHEDULE_WEEKS_TABLE}
            WHERE week_start_date = ?
            """,
            (week_start_date,),
        )
        week = fetchone_dict(cursor)

        if week and week.get("status") == SCHEDULE_STATUS_PUBLISHED and not publish:
            raise ValueError("Published schedules cannot be overwritten by draft save.")

        if week:
            weekly_schedule_id = week["id"]
            if publish:
                cursor.execute(
                    f"""
                    UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
                    SET status = ?,
                        schedule_status = ?,
                        constraints_status = ?,
                        week_end_date = ?,
                        published_at = SYSUTCDATETIME(),
                        updated_at = SYSUTCDATETIME()
                    WHERE id = ?
                    """,
                    (
                        target_status,
                        target_status,
                        CONSTRAINTS_STATUS_CLOSED,
                        _week_end_date(week_start_date),
                        weekly_schedule_id,
                    ),
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
                    SET status = ?,
                        schedule_status = ?,
                        week_end_date = ?,
                        updated_at = SYSUTCDATETIME()
                    WHERE id = ?
                    """,
                    (target_status, target_status, _week_end_date(week_start_date), weekly_schedule_id),
                )
        else:
            published_column = ", published_at" if publish else ""
            published_value = ", SYSUTCDATETIME()" if publish else ""
            cursor.execute(
                f"""
                INSERT INTO {WEEKLY_SCHEDULE_WEEKS_TABLE}
                    (week_start_date, week_end_date, status, schedule_status, constraints_status{published_column})
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?{published_value})
                """,
                (
                    week_start_date,
                    _week_end_date(week_start_date),
                    target_status,
                    target_status,
                    CONSTRAINTS_STATUS_CLOSED if publish else CONSTRAINTS_STATUS_CLOSED,
                ),
            )
            weekly_schedule_id = cursor.fetchone()[0]

        cursor.execute(
            f"""
            DELETE FROM {WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE}
            WHERE weekly_schedule_id = ?
            """,
            (weekly_schedule_id,),
        )

        assignment_params = [
            (
                weekly_schedule_id,
                assignment["employee_email"],
                assignment.get("employee_name"),
                assignment["work_date"],
                assignment["day_name"],
                assignment["shift_type"],
                assignment.get("start_time"),
                assignment.get("end_time"),
                assignment.get("notes"),
            )
            for assignment in assignments
        ]

        if assignment_params:
            insert_query = f"""
            INSERT INTO {WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE} (
                weekly_schedule_id,
                employee_email,
                employee_name,
                work_date,
                day_name,
                shift_type,
                start_time,
                end_time,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if hasattr(cursor, "fast_executemany"):
                cursor.fast_executemany = True
            if hasattr(cursor, "executemany"):
                cursor.executemany(insert_query, assignment_params)
            else:
                for params in assignment_params:
                    cursor.execute(insert_query, params)

        conn.commit()
        return weekly_schedule_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def publish_weekly_schedule(week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT id, COALESCE(schedule_status, status) AS status
            FROM {WEEKLY_SCHEDULE_WEEKS_TABLE}
            WHERE week_start_date = ?
            """,
            (week_start_date,),
        )
        week = fetchone_dict(cursor)

        if not week:
            raise ValueError("No saved weekly schedule exists for this week.")

        cursor.execute(
            f"""
            UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
            SET status = 'published',
                schedule_status = 'published',
                constraints_status = 'closed',
                week_end_date = ?,
                published_at = SYSUTCDATETIME(),
                updated_at = SYSUTCDATETIME()
            WHERE id = ?
            """,
            (_week_end_date(week_start_date), week["id"]),
        )

        conn.commit()
        return week["id"]
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def delete_weekly_schedule_draft(week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT id, COALESCE(schedule_status, status) AS status
            FROM {WEEKLY_SCHEDULE_WEEKS_TABLE}
            WHERE week_start_date = ?
            """,
            (week_start_date,),
        )
        week = fetchone_dict(cursor)

        if not week:
            conn.commit()
            return 0

        cursor.execute(
            f"""
            DELETE FROM {WEEKLY_SCHEDULE_ASSIGNMENTS_TABLE}
            WHERE weekly_schedule_id = ?
            """,
            (week["id"],),
        )
        deleted_count = cursor.rowcount

        cursor.execute(
            f"""
            UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
            SET status = 'draft',
                schedule_status = 'draft',
                week_end_date = ?,
                published_at = NULL,
                updated_at = SYSUTCDATETIME()
            WHERE id = ?
            """,
            (_week_end_date(week_start_date), week["id"]),
        )

        conn.commit()
        return deleted_count
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def ensure_weekly_schedule_week(
    week_start_date,
    schedule_status=SCHEDULE_STATUS_DRAFT,
    constraints_status=CONSTRAINTS_STATUS_CLOSED,
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT id
            FROM {WEEKLY_SCHEDULE_WEEKS_TABLE}
            WHERE week_start_date = ?
            """,
            (week_start_date,),
        )
        week = fetchone_dict(cursor)

        if week:
            cursor.execute(
                f"""
                UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
                SET week_end_date = ?,
                    constraints_status = ?,
                    updated_at = SYSUTCDATETIME()
                WHERE id = ?
                """,
                (_week_end_date(week_start_date), constraints_status, week["id"]),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {WEEKLY_SCHEDULE_WEEKS_TABLE}
                    (week_start_date, week_end_date, status, schedule_status, constraints_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    week_start_date,
                    _week_end_date(week_start_date),
                    schedule_status,
                    schedule_status,
                    constraints_status,
                ),
            )

        conn.commit()
        return get_weekly_schedule_week(week_start_date)
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def set_constraints_status_for_week(week_start_date, constraints_status):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
            SET constraints_status = ?,
                week_end_date = ?,
                updated_at = SYSUTCDATETIME()
            WHERE week_start_date = ?
            """,
            (constraints_status, _week_end_date(week_start_date), week_start_date),
        )

        if cursor.rowcount == 0:
            cursor.execute(
                f"""
                INSERT INTO {WEEKLY_SCHEDULE_WEEKS_TABLE}
                    (week_start_date, week_end_date, status, schedule_status, constraints_status)
                VALUES (?, ?, 'draft', 'draft', ?)
                """,
                (week_start_date, _week_end_date(week_start_date), constraints_status),
            )

        conn.commit()
        return get_weekly_schedule_week(week_start_date)
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def open_constraints_for_week(week_start_date):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
            SET constraints_status = 'closed',
                updated_at = SYSUTCDATETIME()
            WHERE constraints_status = 'open'
              AND week_start_date <> ?
            """,
            (week_start_date,),
        )
        cursor.execute(
            f"""
            UPDATE {WEEKLY_SCHEDULE_WEEKS_TABLE}
            SET constraints_status = 'open',
                week_end_date = ?,
                updated_at = SYSUTCDATETIME()
            WHERE week_start_date = ?
            """,
            (_week_end_date(week_start_date), week_start_date),
        )

        if cursor.rowcount == 0:
            cursor.execute(
                f"""
                INSERT INTO {WEEKLY_SCHEDULE_WEEKS_TABLE}
                    (week_start_date, week_end_date, status, schedule_status, constraints_status)
                VALUES (?, ?, 'draft', 'draft', 'open')
                """,
                (week_start_date, _week_end_date(week_start_date)),
            )

        conn.commit()
        return get_weekly_schedule_week(week_start_date)
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_open_constraints_week():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT TOP 1
                id,
                week_start_date,
                COALESCE(week_end_date, DATEADD(day, 5, week_start_date)) AS week_end_date,
                COALESCE(schedule_status, status) AS status,
                COALESCE(schedule_status, status) AS schedule_status,
                constraints_status,
                created_at,
                updated_at,
                published_at
            FROM {WEEKLY_SCHEDULE_WEEKS_TABLE}
            WHERE constraints_status = 'open'
            ORDER BY updated_at DESC, week_start_date DESC, id DESC
            """,
        )
        return fetchone_dict(cursor)
    finally:
        cursor.close()
        conn.close()
