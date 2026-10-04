from unittest.mock import patch


def test_tour_payment_saves_booking_and_payment(client):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user"] = "Test User"
        session["email"] = "test@example.com"
        session["role"] = "visitor"
        session["tour_booking_draft"] = {
            "tour_title": "סיור בסיסי",
            "selected_date": "2026-06-10",
            "selected_time": "11:00",
            "participants": 6,
            "total_price": 480,
            "full_name": "Test User",
            "phone": "0501234567",
            "email": "test@example.com",
            "notes": ""
        }

    with patch("backend.main.create_tour_booking", return_value=31) as mock_booking, \
         patch("backend.main.create_payment") as mock_payment:

        response = client.post("/tours/payment")

    assert response.status_code == 200
    mock_booking.assert_called_once()
    mock_payment.assert_called_once()

    payment_data = mock_payment.call_args[0][0]
    assert payment_data["booking_id"] == 31
    assert payment_data["amount"] == 480
    assert payment_data["payment_status"] == "Paid"