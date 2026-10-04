from backend.data_access.db import get_connection

def create_payment(payment_data):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO dbo.payments (
                booking_id,
                full_name,
                email,
                amount,
                payment_method,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payment_data.get("booking_id"),
                payment_data.get("full_name"),
                payment_data.get("email"),
                float(payment_data.get("amount") or 0),
                payment_data.get("payment_method", "Credit Card"),
                payment_data.get("payment_status", "Paid"),
            ),
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()


def get_all_payments():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                booking_id,
                full_name,
                email,
                amount,
                payment_method,
                payment_status,
                created_at
            FROM dbo.payments
            ORDER BY created_at DESC
            """
        )

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()