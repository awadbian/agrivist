from backend.data_access.db import get_connection


def get_combined_satisfaction_summary():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                CAST(AVG(CAST(rating AS FLOAT)) AS DECIMAL(3,1)) AS average_rating,
                COUNT(*) AS rating_count
            FROM (
                SELECT rating FROM dbo.website_feedback
                UNION ALL
                SELECT rating FROM dbo.tour_ratings
            ) AS all_ratings
        """)

        row = cursor.fetchone()

        if not row or row[1] == 0:
            return {
                "average_rating": 0,
                "rating_count": 0
            }

        return {
            "average_rating": float(row[0]),
            "rating_count": int(row[1])
        }

    except Exception as exc:
        print(f"Warning: failed to fetch combined satisfaction summary: {exc}")
        return {
            "average_rating": 0,
            "rating_count": 0
        }

    finally:
        cursor.close()
        conn.close()