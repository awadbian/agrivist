from datetime import datetime

from flask import session
from backend import main

app = main.app


def _login_as_employee(client, user_id=17):
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["user"] = "שרה כהן"
        session["email"] = "sara.cohen@gmail.com"
        session["role"] = "employee"


def _login_as_visitor(client):
    with client.session_transaction() as session:
        session["user_id"] = 5
        session["user"] = "Visitor User"
        session["email"] = "visitor@example.com"
        session["role"] = "visitor"


def test_employee_can_view_notifications(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr(
        main,
        "get_user_notifications",
        lambda user_id: [
            {
                "id": 1,
                "user_id": user_id,
                "title": "הזמנה חדשה",
                "message": "התקבלה הזמנת סיור חדשה.",
                "is_read": False,
                "created_at": datetime(2026, 6, 5, 18, 58),
            }
        ],
    )

    with app.test_client() as client:
        _login_as_employee(client)

        response = client.get("/notifications")

    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "ההתראות שלי" in page
    assert "הזמנה חדשה" in page
    assert "התקבלה הזמנת סיור חדשה." in page


def test_logged_out_user_cannot_view_notifications():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/notifications", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert "/login" in response.headers["Location"]


def test_employee_can_mark_notification_as_read(monkeypatch):
    app.config["TESTING"] = True

    marked = {"notification_id": None, "user_id": None}

    def fake_mark_notification_as_read(notification_id, user_id):
        marked["notification_id"] = notification_id
        marked["user_id"] = user_id

    monkeypatch.setattr(main, "mark_notification_as_read", fake_mark_notification_as_read)

    with app.test_client() as client:
        _login_as_employee(client, user_id=17)

        response = client.post(
            "/notifications/3/read",
            follow_redirects=False,
        )

    assert response.status_code in (302, 303)
    assert marked["notification_id"] == 3
    assert marked["user_id"] == 17


def test_employee_notification_count_in_context(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr(main, "get_unread_notifications_count", lambda user_id: 2)
    monkeypatch.setattr(
        main,
        "get_user_notifications",
        lambda user_id: [
            {
                "id": 1,
                "title": "הזמנה חדשה",
                "message": "התקבלה הזמנה חדשה",
                "is_read": False,
                "created_at": None,
            },
            {
                "id": 2,
                "title": "בקשת העבודה אושרה",
                "message": "מזל טוב",
                "is_read": False,
                "created_at": None,
            },
        ],
    )

    with app.test_request_context("/"):
        session["user_id"] = 17
        session["role"] = "employee"

        result = main.inject_notifications_count()

    assert result["unread_notifications_count"] == 2
    assert len(result["header_notifications"]) == 2

def test_visitor_does_not_get_employee_notification_context(monkeypatch):
    app.config["TESTING"] = True

    with app.test_client() as client:
        _login_as_visitor(client)

        with client.session_transaction() as session:
            session["user_id"] = 5
            session["role"] = "visitor"

        with app.test_request_context("/"):
            result = main.inject_notifications_count()

    assert result["unread_notifications_count"] == 0
    assert result["header_notifications"] == []


def test_notify_employees_about_new_booking(monkeypatch):
    app.config["TESTING"] = True

    captured = {"title": None, "message": None}

    def fake_create_notification_for_all_employees(title, message):
        captured["title"] = title
        captured["message"] = message

    monkeypatch.setattr(
        main,
        "create_notification_for_all_employees",
        fake_create_notification_for_all_employees,
    )

    booking_data = {
        "tour_type": "סיור בסיסי",
        "full_name": "דוד כהן",
        "preferred_date": "2026-06-21",
    }

    main.notify_employees_about_new_booking(booking_data)

    assert captured["title"] == "הזמנה חדשה"
    assert "דוד כהן" in captured["message"]
    assert "סיור בסיסי" in captured["message"]
    assert "2026-06-21" in captured["message"]
