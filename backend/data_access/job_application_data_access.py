from backend.data_access.db import get_connection, fetchall_dicts, fetchone_dict

JOB_APPLICATIONS_TABLE = "dbo.job_applications"


def create_job_application(full_name, email, phone, worked_before, experience):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        INSERT INTO {JOB_APPLICATIONS_TABLE}
        (full_name, email, phone, worked_before, experience, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        full_name,
        email,
        phone,
        worked_before,
        experience,
        "pending"
    )

    connection.commit()
    cursor.close()
    connection.close()


def get_all_job_applications():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        SELECT
            id,
            full_name,
            email,
            phone,
            worked_before,
            experience,
            status,
            created_at,
            decided_at
        FROM {JOB_APPLICATIONS_TABLE}
        ORDER BY
            CASE
                WHEN status = 'pending' THEN 1
                WHEN status = 'accepted' THEN 2
                WHEN status = 'rejected' THEN 3
                ELSE 4
            END,
            created_at DESC
        """
    )

    applications = fetchall_dicts(cursor)

    cursor.close()
    connection.close()

    return applications


def get_job_application_by_id(application_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        SELECT
            id,
            full_name,
            email,
            phone,
            worked_before,
            experience,
            status,
            created_at,
            decided_at
        FROM {JOB_APPLICATIONS_TABLE}
        WHERE id = ?
        """,
        application_id
    )

    application = fetchone_dict(cursor)

    cursor.close()
    connection.close()

    return application


def approve_job_application(application_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        UPDATE {JOB_APPLICATIONS_TABLE}
        SET status = 'accepted',
            decided_at = SYSUTCDATETIME()
        WHERE id = ?
        """,
        application_id
    )

    connection.commit()
    cursor.close()
    connection.close()


def reject_job_application(application_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        UPDATE {JOB_APPLICATIONS_TABLE}
        SET status = 'rejected',
            decided_at = SYSUTCDATETIME()
        WHERE id = ?
        """,
        application_id
    )

    connection.commit()
    cursor.close()
    connection.close()