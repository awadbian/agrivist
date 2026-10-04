from unittest.mock import patch
from backend.main import app


def test_tours_booking_page_loads():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/tours-booking")

        assert response.status_code == 200
        assert "סיורים והזמנות" in response.get_data(as_text=True)
        assert "טופס הזמנה" in response.get_data(as_text=True)


def test_tours_booking_requires_login():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.post("/tours-booking", data={
            "tour_type": "סיור בסיסי",
            "full_name": "Test User",
            "phone": "0501234567",
            "email": "test@test.com",
            "preferred_date": "2026-05-20",
            "preferred_time": "12:00",
            "participants": "2",
            "notes": ""
        })

        page = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "עליך להתחבר לפני ביצוע הזמנה" in page
        assert "התחברות לחשבון" in page


def test_tours_booking_email_must_match_logged_user():
    app.config["TESTING"] = True

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["email"] = "realuser@gmail.com"
            session["user"] = "Real User"
            session["role"] = "visitor"

        response = client.post("/tours-booking", data={
            "tour_type": "סיור בסיסי",
            "full_name": "Test User",
            "phone": "0501234567",
            "email": "wrong@gmail.com",
            "preferred_date": "2026-05-20",
            "preferred_time": "12:00",
            "participants": "2",
            "notes": ""
        })

        page = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "ניתן לבצע הזמנה רק עם האימייל של המשתמש המחובר." in page


@patch("backend.main.notify_admins_about_new_booking")
@patch("backend.main.notify_employees_about_new_booking")
@patch("backend.main.create_tour_booking")
def test_tours_booking_success(mock_create_booking, mock_notify_employees, mock_notify_admins):
    app.config["TESTING"] = True
    mock_create_booking.return_value = None
    mock_notify_employees.return_value = None
    mock_notify_admins.return_value = None

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["email"] = "test@test.com"
            session["user"] = "Test User"
            session["role"] = "visitor"

        response = client.post("/tours-booking", data={
            "tour_type": "סיור בסיסי",
            "full_name": "Test User",
            "phone": "0501234567",
            "email": "test@test.com",
            "preferred_date": "2026-05-20",
            "preferred_time": "12:00",
            "participants": "2",
            "notes": ""
        })

        page = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "ההזמנה נשמרה בהצלחה!" in page
        mock_create_booking.assert_called_once()