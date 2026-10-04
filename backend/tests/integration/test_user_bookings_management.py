from datetime import date, timedelta


def test_my_booked_tours_requires_login(client):
    response = client.get("/my-booked-tours", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert "/login" in response.headers.get("Location", "")


def test_my_booked_tours_page_for_logged_in_user(client, monkeypatch):
    with client.session_transaction() as session:
        session["user"] = "Test User"
        session["email"] = "test@example.com"
        session["role"] = "user"

    def fake_get_paid_bookings(email):
        return [
            {
                "id": 1,
                "tour_type": "Pepper Farm Tour",
                "preferred_date": date.today() + timedelta(days=5),
                "preferred_time": "10:00",
                "participants": 2,
                "payment_status": "Paid",
                "status": "active",
                "notes": "",
            }
        ]

    monkeypatch.setattr(
        "backend.main.get_paid_tour_bookings_by_email",
        fake_get_paid_bookings
    )

    response = client.get("/my-booked-tours")

    assert response.status_code == 200
    assert "Pepper Farm Tour".encode("utf-8") in response.data
    assert b"Paid" in response.data
    assert b"Cancel Booking" in response.data


def test_cancel_button_not_shown_less_than_two_days(client, monkeypatch):
    with client.session_transaction() as session:
        session["user"] = "Test User"
        session["email"] = "test@example.com"
        session["role"] = "user"

    def fake_get_paid_bookings(email):
        return [
            {
                "id": 2,
                "tour_type": "Short Notice Tour",
                "preferred_date": date.today() + timedelta(days=1),
                "preferred_time": "12:00",
                "participants": 1,
                "payment_status": "Paid",
                "status": "active",
                "notes": "",
            }
        ]

    monkeypatch.setattr(
        "backend.main.get_paid_tour_bookings_by_email",
        fake_get_paid_bookings
    )

    response = client.get("/my-booked-tours")

    assert response.status_code == 200
    assert b"Cancel Booking" not in response.data
    assert b"Cancellation is allowed only up to 2 days before the tour" in response.data


def test_cancel_booking_success(client, monkeypatch):
    with client.session_transaction() as session:
        session["user"] = "Test User"
        session["email"] = "test@example.com"
        session["role"] = "user"

    def fake_cancel_booking(booking_id, email):
        assert booking_id == 1
        assert email == "test@example.com"
        return True, "ההזמנה בוטלה בהצלחה."

    monkeypatch.setattr(
        "backend.main.cancel_user_tour_booking",
        fake_cancel_booking
    )

    response = client.post("/my-booked-tours/cancel/1", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert "/my-booked-tours" in response.headers.get("Location", "")


def test_cancel_booking_failure(client, monkeypatch):
    with client.session_transaction() as session:
        session["user"] = "Test User"
        session["email"] = "test@example.com"
        session["role"] = "user"

    def fake_cancel_booking(booking_id, email):
        return False, "לא ניתן לבטל הזמנה פחות מיומיים לפני מועד הסיור."

    monkeypatch.setattr(
        "backend.main.cancel_user_tour_booking",
        fake_cancel_booking
    )

    response = client.post("/my-booked-tours/cancel/5", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert "/my-booked-tours" in response.headers.get("Location", "")