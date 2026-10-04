from backend.data_access.db import get_connection


def create_website_feedback(email, full_name, rating, comment):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO dbo.website_feedback (
                email,
                full_name,
                rating,
                comment
            )
            VALUES (?, ?, ?, ?)
        """, (
            email,
            full_name,
            rating,
            comment
        ))

        conn.commit()
        return True, "תודה! המשוב שלך נשמר בהצלחה."

    except Exception as exc:
        conn.rollback()
        print(f"Warning: failed to save website feedback: {exc}")
        return False, "אירעה שגיאה בשמירת המשוב."

    finally:
        cursor.close()
        conn.close()


def get_latest_website_feedback(limit=6):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            SELECT TOP {int(limit)}
                full_name,
                rating,
                comment,
                created_at
            FROM dbo.website_feedback
            WHERE comment IS NOT NULL
              AND LTRIM(RTRIM(comment)) <> ''
            ORDER BY created_at DESC
        """)

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    except Exception as exc:
        print(f"Warning: failed to fetch website feedback: {exc}")
        return []

    finally:
        cursor.close()
        conn.close()


def get_website_feedback_summary():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                CAST(AVG(CAST(rating AS FLOAT)) AS DECIMAL(3,1)) AS average_rating,
                COUNT(*) AS feedback_count
            FROM dbo.website_feedback
        """)

        row = cursor.fetchone()

        if not row or row[1] == 0:
            return {
                "average_rating": 0,
                "feedback_count": 0
            }

        return {
            "average_rating": float(row[0]),
            "feedback_count": int(row[1])
        }

    except Exception as exc:
        print(f"Warning: failed to fetch website feedback summary: {exc}")
        return {
            "average_rating": 0,
            "feedback_count": 0
        }

    finally:
        cursor.close()
        conn.close()