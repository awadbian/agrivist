import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.data_access.db import get_connection

SCHEMA_NAME = "dbo"
TOUR_PACKAGES_TABLE = f"{SCHEMA_NAME}.tour_packages"
TOUR_BOOKINGS_TABLE = f"{SCHEMA_NAME}.tour_bookings"
TOUR_RATINGS_TABLE = f"{SCHEMA_NAME}.tour_ratings"
SCHEMA_NAME = "dbo"
WEBSITE_FEEDBACK_TABLE = f"{SCHEMA_NAME}.website_feedback"
ROLES_TABLE = f"{SCHEMA_NAME}.roles"
USERS_TABLE = f"{SCHEMA_NAME}.users"
PEPPERS_TABLE = f"{SCHEMA_NAME}.peppers"
PEPPER_HEAT_LEVELS_TABLE = f"{SCHEMA_NAME}.pepper_heat_levels"
PAYMENTS_TABLE = f"{SCHEMA_NAME}.payments"
DEFAULT_ROLE_NAME = "visitor"
DEFAULT_ROLES = ("visitor", "admin", "employee")
DEFAULT_HEAT_LEVELS = (
    (0, "No heat", 0, 0, "#52a84f", "heat-none", "No noticeable pepper heat."),
    (1, "Mild", 1, 2500, "#8abf45", "heat-mild", "Low heat suitable for most visitors."),
    (2, "Warm", 2501, 10000, "#e7bd32", "heat-warm", "Noticeable but comfortable pepper heat."),
    (3, "Medium", 10001, 50000, "#e99b2d", "heat-medium", "Balanced pepper heat."),
    (4, "Hot", 50001, 350000, "#d7463f", "heat-hot", "Strong heat for spicy peppers."),
    (5, "Extreme", 350001, 2200000, "#8d1f18", "heat-extreme", "Very intense pepper heat."),
)


def _qualified_table_name(table_name):
    return f"{SCHEMA_NAME}.{table_name}"


def _ensure_column(cursor, table_name, column_name, column_definition):
    cursor.execute(
        "SELECT COL_LENGTH(?, ?) AS column_length",
        (_qualified_table_name(table_name), column_name),
    )
    row = cursor.fetchone()
    if row is None or row[0] is None:
        cursor.execute(
            f"ALTER TABLE {_qualified_table_name(table_name)} "
            f"ADD {column_name} {column_definition}"
        )


def _column_exists(cursor, table_name, column_name):
    cursor.execute(
        "SELECT COL_LENGTH(?, ?) AS column_length",
        (_qualified_table_name(table_name), column_name),
    )
    row = cursor.fetchone()
    return row is not None and row[0] is not None


def _constraint_exists(cursor, constraint_name):
    cursor.execute(
        """
        SELECT 1
        FROM sys.foreign_keys
        WHERE name = ?
        """,
        (constraint_name,),
    )
    return cursor.fetchone() is not None


def _seed_roles(cursor):
    for role_name in DEFAULT_ROLES:
        cursor.execute(
            f"""
            IF NOT EXISTS (SELECT 1 FROM {ROLES_TABLE} WHERE name = ?)
            INSERT INTO {ROLES_TABLE} (name)
            VALUES (?)
            """,
            (role_name, role_name),
        )


def _seed_heat_levels(cursor):
    for level_value, name, min_scoville, max_scoville, color, css_class, description in DEFAULT_HEAT_LEVELS:
        cursor.execute(
            f"""
            IF NOT EXISTS (SELECT 1 FROM {PEPPER_HEAT_LEVELS_TABLE} WHERE name = ?)
            INSERT INTO {PEPPER_HEAT_LEVELS_TABLE}
                (level_value, name, min_scoville, max_scoville, color, css_class, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ELSE
            UPDATE {PEPPER_HEAT_LEVELS_TABLE}
            SET level_value = ?,
                min_scoville = ?,
                max_scoville = ?,
                color = ?,
                css_class = ?,
                description = ?
            WHERE name = ?
            """,
            (
                name,
                level_value, name, min_scoville, max_scoville, color, css_class, description,
                level_value, min_scoville, max_scoville, color, css_class, description, name,
            ),
        )


def _drop_users_role_default_constraint(cursor):
    cursor.execute(f"""
    DECLARE @constraint_name sysname;
    DECLARE @sql NVARCHAR(MAX);

    SELECT @constraint_name = default_constraints.name
    FROM sys.default_constraints
    INNER JOIN sys.columns
        ON columns.default_object_id = default_constraints.object_id
    INNER JOIN sys.tables
        ON tables.object_id = columns.object_id
    INNER JOIN sys.schemas
        ON schemas.schema_id = tables.schema_id
    WHERE schemas.name = '{SCHEMA_NAME}'
        AND tables.name = 'users'
        AND columns.name = 'role';

    IF @constraint_name IS NOT NULL
    BEGIN
        SET @sql = N'ALTER TABLE {USERS_TABLE} DROP CONSTRAINT ' + QUOTENAME(@constraint_name);
        EXEC sp_executesql @sql;
    END
    """)


def _migrate_users_role_column(cursor):
    if not _column_exists(cursor, "users", "role_id"):
        cursor.execute(f"ALTER TABLE {USERS_TABLE} ADD role_id INT NULL")

    if _column_exists(cursor, "users", "role"):
        cursor.execute(
            f"""
            UPDATE user_rows
            SET role_id = roles.id
            FROM {USERS_TABLE} AS user_rows
            INNER JOIN {ROLES_TABLE} AS roles
                ON roles.name = LOWER(LTRIM(RTRIM(user_rows.role)))
            WHERE user_rows.role_id IS NULL
                AND user_rows.role IS NOT NULL
                AND LTRIM(RTRIM(user_rows.role)) <> ''
            """
        )

    cursor.execute(
        f"""
        UPDATE user_rows
        SET role_id = roles.id
        FROM {USERS_TABLE} AS user_rows
        INNER JOIN {ROLES_TABLE} AS roles
            ON roles.name = ?
        WHERE user_rows.role_id IS NULL
        """,
        (DEFAULT_ROLE_NAME,),
    )

    cursor.execute(f"ALTER TABLE {USERS_TABLE} ALTER COLUMN role_id INT NOT NULL")

    if not _constraint_exists(cursor, "FK_users_roles"):
        cursor.execute(f"""
        ALTER TABLE {USERS_TABLE}
        ADD CONSTRAINT FK_users_roles
        FOREIGN KEY (role_id) REFERENCES {ROLES_TABLE}(id)
        """)

    if _column_exists(cursor, "users", "role"):
        _drop_users_role_default_constraint(cursor)
        cursor.execute(f"ALTER TABLE {USERS_TABLE} DROP COLUMN role")


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
        IF OBJECT_ID('{ROLES_TABLE}', 'U') IS NULL
        CREATE TABLE {ROLES_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            name NVARCHAR(50) NOT NULL UNIQUE
        )
        """)

        _seed_roles(cursor)

        cursor.execute(f"""
        IF OBJECT_ID('{USERS_TABLE}', 'U') IS NULL
        CREATE TABLE {USERS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            full_name NVARCHAR(255) NOT NULL,
            email NVARCHAR(255) NOT NULL UNIQUE,
            password_hash NVARCHAR(255) NOT NULL,
            role_id INT NOT NULL
        )
        """)

        _migrate_users_role_column(cursor)
        _ensure_column(cursor, "users", "phone", "NVARCHAR(20)")
        _ensure_column(cursor, "users", "city", "NVARCHAR(100)")
        _ensure_column(cursor, "users", "about", "NVARCHAR(500)")
        _ensure_column(cursor, "users", "is_active", "BIT NOT NULL DEFAULT 1")
        _ensure_column(cursor, "users", "created_at", "DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()")

        cursor.execute(f"""
        IF OBJECT_ID('{PEPPER_HEAT_LEVELS_TABLE}', 'U') IS NULL
        CREATE TABLE {PEPPER_HEAT_LEVELS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            level_value INT NOT NULL,
            name NVARCHAR(100) NOT NULL UNIQUE,
            min_scoville INT NOT NULL,
            max_scoville INT NOT NULL,
            color NVARCHAR(20) NOT NULL,
            css_class NVARCHAR(100) NOT NULL,
            description NVARCHAR(MAX)
        )
        """)
        _ensure_column(cursor, "pepper_heat_levels", "level_value", "INT")
        _seed_heat_levels(cursor)

        cursor.execute(f"""
        IF OBJECT_ID('{PEPPERS_TABLE}', 'U') IS NULL
        CREATE TABLE {PEPPERS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            name NVARCHAR(255) NOT NULL,
            scientific_name NVARCHAR(255),
            origin_country NVARCHAR(255),
            color NVARCHAR(100),
            scoville_level NVARCHAR(100) NOT NULL,
            heat_level_id INT,
            heat_category NVARCHAR(100),
            description NVARCHAR(MAX) NOT NULL,
            culinary_tips NVARCHAR(MAX),
            growing_tips NVARCHAR(MAX),
            warnings NVARCHAR(MAX),
            image_url NVARCHAR(2048),
            status NVARCHAR(50),
            spray_info NVARCHAR(MAX),
            watering_needs NVARCHAR(MAX),
            sunlight_needs NVARCHAR(MAX),
            season NVARCHAR(100),
            use_cases NVARCHAR(MAX),
            extra_info NVARCHAR(MAX)
        )
        """)
        cursor.execute(f"""
        IF OBJECT_ID('{TOUR_BOOKINGS_TABLE}', 'U') IS NULL
        CREATE TABLE {TOUR_BOOKINGS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            tour_type NVARCHAR(100) NOT NULL,
            full_name NVARCHAR(255) NOT NULL,
            phone NVARCHAR(50) NOT NULL,
            email NVARCHAR(255) NOT NULL,
            preferred_date DATE NOT NULL,
            preferred_time TIME NOT NULL,
            participants INT NOT NULL,
            notes NVARCHAR(MAX),
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
        )
        """)
        _ensure_column(cursor, "tour_bookings", "status", "NVARCHAR(30) NOT NULL DEFAULT 'active'")
        _ensure_column(cursor, "tour_bookings", "payment_status", "NVARCHAR(30) NOT NULL DEFAULT 'Pending'")
        _ensure_column(cursor, "tour_bookings", "total_price", "DECIMAL(10,2) NOT NULL DEFAULT 0")
        _ensure_column(cursor, "tour_bookings", "paid_at", "DATETIME2 NULL")
        _ensure_column(cursor, "tour_bookings", "assigned_worker_id", "INT NULL")

        cursor.execute(f"""
        IF OBJECT_ID('{TOUR_RATINGS_TABLE}', 'U') IS NULL
        CREATE TABLE {TOUR_RATINGS_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            booking_id INT NOT NULL,
            email NVARCHAR(255) NOT NULL,
            full_name NVARCHAR(255),
            tour_type NVARCHAR(100) NOT NULL,
            rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment NVARCHAR(MAX),
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            CONSTRAINT UQ_tour_ratings_booking UNIQUE (booking_id)
        )
        """)

        cursor.execute("""
        IF OBJECT_ID('dbo.payments', 'U') IS NULL
        CREATE TABLE dbo.payments (
            id INT IDENTITY(1,1) PRIMARY KEY,
            booking_id INT NOT NULL,
            full_name NVARCHAR(255) NOT NULL,
            email NVARCHAR(255) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            payment_method NVARCHAR(50) NOT NULL,
            payment_status NVARCHAR(30) NOT NULL DEFAULT 'Paid',
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
)
""")
        cursor.execute("""
IF OBJECT_ID('dbo.payments', 'U') IS NULL
CREATE TABLE dbo.payments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    booking_id INT NOT NULL,
    full_name NVARCHAR(255) NOT NULL,
    email NVARCHAR(255) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method NVARCHAR(50) NOT NULL,
    payment_status NVARCHAR(30) NOT NULL DEFAULT 'Paid',
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
)
""")
        cursor.execute(f"""
IF OBJECT_ID('{TOUR_PACKAGES_TABLE}', 'U') IS NULL
CREATE TABLE {TOUR_PACKAGES_TABLE} (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(100) NOT NULL,
    price INT NOT NULL,
    duration NVARCHAR(50) NOT NULL,
    duration_minutes INT NULL,
    max_people INT NOT NULL,
    description NVARCHAR(MAX) NOT NULL,
    includes NVARCHAR(MAX) NOT NULL,
    image_url NVARCHAR(2048),
    available_from DATE,
    available_until DATE,
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
)
""")
        _ensure_column(cursor, "tour_packages", "duration", "NVARCHAR(50)")
        _ensure_column(cursor, "tour_packages", "duration_minutes", "INT")
        _ensure_column(cursor, "tour_packages", "image_url", "NVARCHAR(2048)")
        _ensure_column(cursor, "tour_packages", "available_from", "DATE")
        _ensure_column(cursor, "tour_packages", "available_until", "DATE")
        _ensure_column(cursor, "tour_packages", "is_active", "BIT NOT NULL DEFAULT 1")
        _ensure_column(cursor, "tour_packages", "created_at", "DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()")
        cursor.execute(f"""
        UPDATE {TOUR_PACKAGES_TABLE}
        SET duration_minutes = CASE
            WHEN duration_minutes IS NOT NULL THEN duration_minutes
            WHEN duration LIKE N'%חצי%' THEN 90
            WHEN duration LIKE N'%3%' THEN 180
            WHEN duration LIKE N'%שעתיים%' THEN 120
            ELSE 90
        END
        WHERE duration_minutes IS NULL
        """)
        cursor.execute(f"""
IF NOT EXISTS (SELECT 1 FROM {TOUR_PACKAGES_TABLE})
BEGIN
    INSERT INTO {TOUR_PACKAGES_TABLE}
    (title, price, duration, duration_minutes, max_people, description, includes)

    VALUES
    (
        N'סיור בסיסי',
        80,
        N'שעה וחצי',
        90,
        20,
        N'סיור מודרך בחווה, הכרות עם זני הפלפלים העיקריים וסיפור החווה',
        N'הדרכה מקצועית
סיור בחממות
טעימות פלפלים
תמונות מזכרת'
    ),

    (
        N'סיור משפחתי',
        120,
        N'שעתיים',
        120,
        15,
        N'סיור מותאם למשפחות עם פעילויות לילדים וסדנת הכנת רטבים',
        N'פעילויות לילדים
סדנת הכנת רטבים
טעימות והדגמות
מתנות לילדים'
    ),

    (
        N'חוויה פרימיום',
        200,
        N'3 שעות',
        180,
        12,
        N'סיור מעמיק כולל סדנת קטיף, הכנת רטבים וארוחה חקלאית',
        N'סדנת קטיף בחממות
הכנת רטבים אישית
ארוחה חקלאית
מוצרי החווה'
    )
END
""")
        _ensure_column(cursor, "peppers", "scientific_name", "NVARCHAR(255)")
        _ensure_column(cursor, "peppers", "origin_country", "NVARCHAR(255)")
        _ensure_column(cursor, "peppers", "heat_level_id", "INT")
        _ensure_column(cursor, "peppers", "heat_category", "NVARCHAR(100)")
        _ensure_column(cursor, "peppers", "culinary_tips", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "growing_tips", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "warnings", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "status", "NVARCHAR(50)")
        _ensure_column(cursor, "peppers", "spray_info", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "watering_needs", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "sunlight_needs", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "season", "NVARCHAR(100)")
        _ensure_column(cursor, "peppers", "use_cases", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "extra_info", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "soil_type", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "temperature_range", "NVARCHAR(100)")
        _ensure_column(cursor, "peppers", "irrigation_frequency", "NVARCHAR(100)")
        _ensure_column(cursor, "peppers", "water_amount", "NVARCHAR(100)")
        _ensure_column(cursor, "peppers", "harvest_season", "NVARCHAR(100)")
        _ensure_column(cursor, "peppers", "days_to_harvest", "INT")
        _ensure_column(cursor, "peppers", "harvest_signs", "NVARCHAR(MAX)")
        _ensure_column(cursor, "peppers", "storage_tips", "NVARCHAR(MAX)")

        if not _constraint_exists(cursor, "FK_peppers_heat_levels"):
            cursor.execute(f"""
            ALTER TABLE {PEPPERS_TABLE}
            ADD CONSTRAINT FK_peppers_heat_levels
            FOREIGN KEY (heat_level_id) REFERENCES {PEPPER_HEAT_LEVELS_TABLE}(id)
            """)

        cursor.execute(f"""
        IF OBJECT_ID('{WEBSITE_FEEDBACK_TABLE}', 'U') IS NULL
        CREATE TABLE {WEBSITE_FEEDBACK_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            email NVARCHAR(255) NOT NULL,
            full_name NVARCHAR(255) NOT NULL,
            rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment NVARCHAR(MAX),
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
        )
        """)


        cursor.execute("""
        IF OBJECT_ID('dbo.job_applications', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.job_applications (
                id INT IDENTITY(1,1) PRIMARY KEY,
                full_name NVARCHAR(255) NOT NULL,
                email NVARCHAR(255) NOT NULL,
                phone NVARCHAR(50) NOT NULL,
                worked_before BIT NOT NULL DEFAULT 0,
                experience NVARCHAR(MAX) NOT NULL,
                status NVARCHAR(50) NOT NULL DEFAULT 'pending',
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
                decided_at DATETIME2 NULL
            )
        END
        """)

        _ensure_column(cursor, "job_applications", "status", "NVARCHAR(50) NOT NULL DEFAULT 'pending'")
        _ensure_column(cursor, "job_applications", "created_at", "DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()")
        _ensure_column(cursor, "job_applications", "decided_at", "DATETIME2 NULL")

     
        cursor.execute("""
        IF OBJECT_ID('dbo.notifications', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.notifications (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                title NVARCHAR(255) NOT NULL,
                message NVARCHAR(MAX) NOT NULL,
                is_read BIT NOT NULL DEFAULT 0,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
            )
        END
        """)

        _ensure_column(cursor, "notifications", "user_id", "INT NOT NULL DEFAULT 0")
        _ensure_column(cursor, "notifications", "title", "NVARCHAR(255) NOT NULL DEFAULT ''")
        _ensure_column(cursor, "notifications", "message", "NVARCHAR(MAX) NOT NULL DEFAULT ''")
        _ensure_column(cursor, "notifications", "is_read", "BIT NOT NULL DEFAULT 0")
        _ensure_column(cursor, "notifications", "created_at", "DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()")


        conn.commit()

    finally:
        cursor.close()
        conn.close()

print("Roles, users, peppers, and pepper heat level tables are ready.")


if __name__ == "__main__":
    create_tables()
