from backend.data_access.db import get_connection
from datetime import datetime, date

def find_available_worker_id(cursor, preferred_date, preferred_time):
    cursor.execute(
        """
        SELECT TOP 1 u.id
        FROM dbo.employee_shifts s
        JOIN dbo.users u ON LOWER(u.email) = LOWER(s.employee_email)
        WHERE u.role_id = 3
          AND s.status = 'Scheduled'
          AND s.day = DATENAME(WEEKDAY, ?)
          AND CAST(? AS time) >= CAST(s.start_time AS time)
          AND CAST(? AS time) < CAST(s.end_time AS time)
        ORDER BY u.id
        """,
        (preferred_date, preferred_time, preferred_time)
    )

    row = cursor.fetchone()
    return row[0] if row else None

def create_tour_booking(form):
    conn = get_connection()
    cursor = conn.cursor()
    assigned_worker_id = find_available_worker_id(
    cursor,
    form.get("preferred_date"),
    form.get("preferred_time")
)


    try:
        cursor.execute(
            """
            INSERT INTO dbo.tour_bookings (
                tour_type,
                full_name,
                phone,
                email,
                preferred_date,
                preferred_time,
                participants,
                notes,
                total_price,
                payment_status,
                assigned_worker_id,
                paid_at
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
            """,
            (
                form.get("tour_type"),
                form.get("full_name"),
                form.get("phone"),
                form.get("email"),
                form.get("preferred_date"),
                form.get("preferred_time"),
                int(form.get("participants")),
                form.get("notes"),
                float(form.get("total_price") or 0),
                form.get("payment_status", "Pending"),
                assigned_worker_id,
            ),
        )

        booking_id = cursor.fetchone()[0]
        conn.commit()
        return booking_id

    finally:
        cursor.close()
        conn.close()

def get_all_tour_bookings():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                tour_type,
                full_name,
                phone,
                email,
                preferred_date,
                preferred_time,
                participants,
                notes,
                created_at,
                status
            FROM dbo.tour_bookings
            ORDER BY created_at DESC
        """)

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()


def cancel_tour_booking_by_id(booking_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE dbo.tour_bookings
            SET status = 'cancelled'
            WHERE id = ?
        """, (booking_id,))

        conn.commit()

    finally:
        cursor.close()
        conn.close() 



def has_active_paid_bookings_for_tour(tour_title):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM dbo.tour_bookings
            WHERE tour_type = ?
              AND status != 'cancelled'
        """, (tour_title,))

        count = cursor.fetchone()[0]
        return count > 0

    finally:
        cursor.close()
        conn.close()  

def get_paid_tour_bookings_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                tour_type,
                full_name,
                phone,
                email,
                preferred_date,
                preferred_time,
                participants,
                notes,
                created_at,
                status,
                payment_status
            FROM dbo.tour_bookings
            WHERE LOWER(email) = LOWER(?)
              AND payment_status = 'Paid'
            ORDER BY preferred_date DESC, preferred_time DESC
        """, (email,))

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()

def cancel_user_tour_booking(booking_id, email):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, email, preferred_date, status
            FROM dbo.tour_bookings
            WHERE id = ?
              AND LOWER(email) = LOWER(?)
              AND payment_status = 'Paid'
        """, (booking_id, email))

        row = cursor.fetchone()

        if not row:
            return False, "ההזמנה לא נמצאה או שאינה שייכת למשתמש שלך."

        preferred_date = row.preferred_date
        current_status = row.status

        if current_status == "Cancelled":
            return False, "ההזמנה כבר מבוטלת."

        if isinstance(preferred_date, str):
            tour_date = datetime.strptime(preferred_date, "%Y-%m-%d").date()
        else:
            tour_date = preferred_date

        days_left = (tour_date - date.today()).days

        if days_left < 2:
            return False, "לא ניתן לבטל הזמנה פחות מיומיים לפני מועד הסיור."

        cursor.execute("""
            UPDATE dbo.tour_bookings
            SET status = 'Cancelled'
            WHERE id = ?
              AND LOWER(email) = LOWER(?)
        """, (booking_id, email))

        conn.commit()

        return True, "ההזמנה בוטלה בהצלחה."

    except Exception as exc:
        conn.rollback()
        return False, f"שגיאה בביטול ההזמנה: {exc}"

    finally:
        cursor.close()
        conn.close()