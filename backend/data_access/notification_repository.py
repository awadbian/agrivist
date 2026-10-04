from backend.data_access.db import get_connection, fetchall_dicts


def create_notification(user_id, title, message):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO dbo.notifications (user_id, title, message, is_read)
        VALUES (?, ?, ?, 0)
        """,
        user_id,
        title,
        message,
    )

    connection.commit()
    cursor.close()
    connection.close()


def get_user_notifications(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, user_id, title, message, is_read, created_at
        FROM dbo.notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        user_id,
    )

    notifications = fetchall_dicts(cursor)

    cursor.close()
    connection.close()

    return notifications


def get_unread_notifications_count(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS unread_count
        FROM dbo.notifications
        WHERE user_id = ? AND is_read = 0
        """,
        user_id,
    )

    row = cursor.fetchone()
    unread_count = row[0] if row else 0

    cursor.close()
    connection.close()

    return unread_count


def mark_notification_as_read(notification_id, user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE dbo.notifications
        SET is_read = 1
        WHERE id = ? AND user_id = ?
        """,
        notification_id,
        user_id,
    )

    connection.commit()
    cursor.close()
    connection.close()


def create_notification_for_all_employees(title, message):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM dbo.users
        WHERE role_id = 3
    """)

    employees = cursor.fetchall()

    for employee in employees:
        cursor.execute(
            """
            INSERT INTO dbo.notifications (user_id, title, message, is_read)
            VALUES (?, ?, ?, 0)
            """,
            employee[0],
            title,
            message,
        )

    connection.commit()
    cursor.close()
    connection.close()


def create_notification_for_all_admins(title, message):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM dbo.users
        WHERE role_id = 2
    """)

    admins = cursor.fetchall()

    for admin in admins:
        cursor.execute(
            """
            INSERT INTO dbo.notifications (user_id, title, message, is_read)
            VALUES (?, ?, ?, 0)
            """,
            admin[0],
            title,
            message,
        )

    connection.commit()
    cursor.close()
    connection.close()