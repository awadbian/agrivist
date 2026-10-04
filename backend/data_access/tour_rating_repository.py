from backend.data_access.db import get_connection


def get_pending_tour_rating_for_user(email):
    if not email:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT TOP 1
                b.id AS booking_id,
                b.tour_type,
                b.preferred_date,
                b.preferred_time,
                b.participants,
                b.email,
                b.full_name
            FROM dbo.tour_bookings b
            LEFT JOIN dbo.tour_ratings r ON r.booking_id = b.id
            WHERE LOWER(b.email) = LOWER(?)
              AND b.payment_status = 'Paid'
              AND ISNULL(b.status, 'active') <> 'Cancelled'
              AND CAST(b.preferred_date AS DATE) <= CAST(GETDATE() AS DATE)
              AND r.id IS NULL
            ORDER BY b.preferred_date DESC, b.preferred_time DESC
        """, (email,))

        row = cursor.fetchone()
        if not row:
            return None

        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

    except Exception as exc:
        print(f"Warning: failed to fetch pending tour rating: {exc}")
        return None

    finally:
        cursor.close()
        conn.close()


def create_tour_rating(email, booking_id, rating, comment):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT TOP 1
                id,
                tour_type,
                full_name
            FROM dbo.tour_bookings
            WHERE id = ?
              AND LOWER(email) = LOWER(?)
              AND payment_status = 'Paid'
              AND ISNULL(status, 'active') <> 'Cancelled'
              AND CAST(preferred_date AS DATE) <= CAST(GETDATE() AS DATE)
        """, (booking_id, email))

        booking = cursor.fetchone()
        if not booking:
            return False, "לא נמצאה הזמנה מתאימה לדירוג."

        tour_type = booking[1]
        full_name = booking[2]

        cursor.execute("""
            SELECT id
            FROM dbo.tour_ratings
            WHERE booking_id = ?
        """, (booking_id,))

        if cursor.fetchone():
            return False, "כבר דירגת את הסיור הזה."

        cursor.execute("""
            INSERT INTO dbo.tour_ratings (
                booking_id,
                email,
                full_name,
                tour_type,
                rating,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            booking_id,
            email,
            full_name,
            tour_type,
            rating,
            comment
        ))

        conn.commit()
        return True, "תודה! הדירוג שלך נשמר בהצלחה."

    except Exception as exc:
        conn.rollback()
        print(f"Warning: failed to create tour rating: {exc}")
        return False, "אירעה שגיאה בשמירת הדירוג."

    finally:
        cursor.close()
        conn.close()


def get_latest_tour_ratings(limit=6):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            SELECT TOP {int(limit)}
                full_name,
                tour_type,
                rating,
                comment,
                created_at
            FROM dbo.tour_ratings
            WHERE comment IS NOT NULL
              AND LTRIM(RTRIM(comment)) <> ''
            ORDER BY created_at DESC
        """)

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    except Exception as exc:
        print(f"Warning: failed to fetch latest tour ratings: {exc}")
        return []

    finally:
        cursor.close()
        conn.close()


def get_tour_rating_summary():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                tour_type,
                CAST(AVG(CAST(rating AS FLOAT)) AS DECIMAL(3,1)) AS average_rating,
                COUNT(*) AS review_count
            FROM dbo.tour_ratings
            GROUP BY tour_type
        """)

        result = {}
        for row in cursor.fetchall():
            result[row[0]] = {
                "average_rating": float(row[1]),
                "review_count": int(row[2])
            }

        return result

    except Exception as exc:
        print(f"Warning: failed to fetch tour rating summary: {exc}")
        return {}

    finally:
        cursor.close()
        conn.close()