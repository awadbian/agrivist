from backend.data_access.db import get_connection, fetchall_dicts, fetchone_dict

EMPLOYEE_PROFILES_TABLE = "dbo.employee_profiles"
EMPLOYEE_SHIFTS_TABLE = "dbo.employee_shifts"
EMPLOYEE_ATTENDANCE_TABLE = "dbo.employee_attendance"

def create_employee_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
    IF OBJECT_ID('{EMPLOYEE_PROFILES_TABLE}', 'U') IS NULL
    CREATE TABLE {EMPLOYEE_PROFILES_TABLE} (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        email NVARCHAR(255) NOT NULL UNIQUE,
        password NVARCHAR(100) NOT NULL,
        role NVARCHAR(50) NOT NULL,
        status NVARCHAR(50) NOT NULL,
        hourly_rate FLOAT NOT NULL
    )
    """)

    cursor.execute(f"""
    IF OBJECT_ID('{EMPLOYEE_SHIFTS_TABLE}', 'U') IS NULL
    CREATE TABLE {EMPLOYEE_SHIFTS_TABLE} (
        id INT IDENTITY(1,1) PRIMARY KEY,
        employee_email NVARCHAR(255) NOT NULL,
        day NVARCHAR(50) NOT NULL,
        start_time NVARCHAR(10) NOT NULL,
        end_time NVARCHAR(10) NOT NULL,
        break_time NVARCHAR(50) NOT NULL,
        status NVARCHAR(50) NOT NULL
    )
    """)

    cursor.execute(f"""
    IF OBJECT_ID('{EMPLOYEE_ATTENDANCE_TABLE}', 'U') IS NULL
    CREATE TABLE {EMPLOYEE_ATTENDANCE_TABLE} (
        id INT IDENTITY(1,1) PRIMARY KEY,
        employee_email NVARCHAR(255) NOT NULL,
        work_date DATE NOT NULL,
        start_shift NVARCHAR(10) NOT NULL,
        end_shift NVARCHAR(10) NULL,
        worked_hours FLOAT NOT NULL DEFAULT 0,
        daily_salary FLOAT NOT NULL DEFAULT 0,
        is_on_duty BIT NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT GETDATE()
    )
    """)
    conn.commit()
    conn.close()


def seed_employees_if_empty(default_employees=None):
    return


def load_employees_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT name, email, password, role, status, hourly_rate
        FROM {EMPLOYEE_PROFILES_TABLE}
        ORDER BY id
    """)
    employees = fetchall_dicts(cursor)

    for employee in employees:
        cursor.execute(
            f"""
            SELECT day, start_time, end_time, break_time, status
            FROM {EMPLOYEE_SHIFTS_TABLE}
            WHERE LOWER(employee_email) = LOWER(?)
            ORDER BY id
            """,
            (employee["email"],),
        )

        rows = fetchall_dicts(cursor)

        employee["attendance"] = {
            "is_on_duty": False,
            "start_shift": None,
            "end_shift": None,
            "worked_hours": 0,
            "daily_salary": 0,
        }

        employee["shifts"] = [
            {
                "day": row["day"],
                "start": row["start_time"],
                "end": row["end_time"],
                "break_time": row["break_time"],
                "status": row["status"],
            }
            for row in rows
        ]

    conn.close()
    return employees

def get_employee_from_db(email):
    employees = load_employees_from_db()

    for employee in employees:
        if employee["email"].lower() == email.lower():
            return employee

    return None


def update_employee_schedule_in_db(email, hourly_rate, shifts):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        email = email.strip().lower()

        cursor.execute(
            f"""
            UPDATE {EMPLOYEE_PROFILES_TABLE}
            SET hourly_rate = ?
            WHERE LOWER(email) = LOWER(?)
            """,
            (hourly_rate, email),
        )

        cursor.execute(
            f"""
            DELETE FROM {EMPLOYEE_SHIFTS_TABLE}
            WHERE LOWER(employee_email) = LOWER(?)
            """,
            (email,),
        )

        for shift in shifts:
            cursor.execute(
                f"""
                INSERT INTO {EMPLOYEE_SHIFTS_TABLE}
                (employee_email, day, start_time, end_time, break_time, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    email,
                    shift["day"],
                    shift["start"],
                    shift["end"],
                    shift["break_time"],
                    shift.get("status", "Scheduled"),
                ),
            )

        conn.commit()

    finally:
        cursor.close()
        conn.close()

def start_employee_shift_in_db(email, start_shift):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            INSERT INTO {EMPLOYEE_ATTENDANCE_TABLE}
            (
                employee_email,
                work_date,
                start_shift,
                end_shift,
                worked_hours,
                daily_salary,
                is_on_duty
            )
            VALUES (
                ?,
                CAST(GETDATE() AS DATE),
                ?,
                NULL,
                0,
                0,
                1
            )
            """,
            (email, start_shift),
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()


def end_employee_shift_in_db(email, end_shift, worked_hours, daily_salary):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            UPDATE {EMPLOYEE_ATTENDANCE_TABLE}
            SET
                end_shift = ?,
                worked_hours = ?,
                daily_salary = ?,
                is_on_duty = 0
            WHERE id = (
                SELECT TOP 1 id
                FROM {EMPLOYEE_ATTENDANCE_TABLE}
                WHERE employee_email = ?
                  AND is_on_duty = 1
                ORDER BY id DESC
            )
            """,
            (
                end_shift,
                worked_hours,
                daily_salary,
                email,
            ),
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()


def get_employee_attendance_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT
                employee_email,
                work_date,
                start_shift,
                end_shift,
                worked_hours,
                daily_salary,
                is_on_duty
            FROM {EMPLOYEE_ATTENDANCE_TABLE}
            ORDER BY id DESC
            """
        )

        rows = fetchall_dicts(cursor)
        result = {}

        for row in rows:
            email = row["employee_email"].lower()

            if email not in result:
                result[email] = {
                    "is_on_duty": False,
                    "start_shift": None,
                    "end_shift": None,
                    "worked_hours": 0,
                    "daily_salary": 0,
                    "history": []
                }

            if row["is_on_duty"]:
                result[email]["is_on_duty"] = True
                result[email]["start_shift"] = row["start_shift"]
                result[email]["end_shift"] = row["end_shift"]
                result[email]["worked_hours"] = row["worked_hours"]
                result[email]["daily_salary"] = row["daily_salary"]
            else:
                result[email]["history"].append({
                    "date": str(row["work_date"]),
                    "start_shift": row["start_shift"],
                    "end_shift": row["end_shift"],
                    "worked_hours": row["worked_hours"],
                    "daily_salary": row["daily_salary"]
                })

        return result

    finally:
        cursor.close()
        conn.close()

def sync_employee_profiles_from_users():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            INSERT INTO {EMPLOYEE_PROFILES_TABLE}
            (name, email, password, role, status, hourly_rate)
            SELECT
                u.full_name,
                LOWER(u.email),
                '',
                'employee',
                N'לא במשמרת',
                40
            FROM dbo.users u
            WHERE u.role_id = 3
              AND u.is_active = 1
              AND NOT EXISTS (
                  SELECT 1
                  FROM {EMPLOYEE_PROFILES_TABLE} p
                  WHERE LOWER(p.email) = LOWER(u.email)
              )
        """)
        conn.commit()

    finally:
        cursor.close()
        conn.close()