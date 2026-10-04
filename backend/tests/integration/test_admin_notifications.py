from datetime import datetime

from flask import session

from backend import main


app = main.app


def _login_as_admin(client, user_id=2):
    with client.session_transaction() as session_data:
        session_data["user_id"] = user_id
        session_data["user"] = "System Admin"
        session_data["email"] = "admin@gmail.com"
        session_data["role"] = "admin"


def _login_as_visitor(client, user_id=5):
    with client.session_transaction() as session_data:
        session_data["user_id"] = user_id
        session_data["user"] = "Visitor User"
        session_data["email"] = "visitor@example.com"
        session_data["role"] = "visitor"


def test_admin_can_view_notifications(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr(
        main,
        "get_user_notifications",
        lambda user_id: [
            {
                "id": 1,
                "user_id": user_id,
                "title": "משתמש חדש נרשם",
                "message": "המשתמש נועה ישראלי נרשם למערכת.",
                "is_read": False,
                "created_at": datetime(2026, 6, 6, 10, 30),
            }
        ],
    )

    with app.test_client() as client:
        _login_as_admin(client)

        response = client.get("/notifications")

    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "ההתראות שלי" in page
    assert "משתמש חדש נרשם" in page
    assert "נועה ישראלי" in page


def test_visitor_cannot_view_admin_notifications():
    app.config["TESTING"] = True

    with app.test_client() as client:
        _login_as_visitor(client)

        response = client.get("/notifications", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert response.headers["Location"].endswith("/")


def test_logged_out_user_redirected_from_notifications():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/notifications", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert "/login" in response.headers["Location"]


def test_admin_can_mark_notification_as_read(monkeypatch):
    app.config["TESTING"] = True

    marked = {"notification_id": None, "user_id": None}

    def fake_mark_notification_as_read(notification_id, user_id):
        marked["notification_id"] = notification_id
        marked["user_id"] = user_id

    monkeypatch.setattr(main, "mark_notification_as_read", fake_mark_notification_as_read)

    with app.test_client() as client:
        _login_as_admin(client, user_id=2)

        response = client.post("/notifications/7/read", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert marked["notification_id"] == 7
    assert marked["user_id"] == 2


def test_admin_notification_count_in_context(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr(main, "get_unread_notifications_count", lambda user_id: 3)
    monkeypatch.setattr(
        main,
        "get_user_notifications",
        lambda user_id: [
            {
                "id": 1,
                "title": "משתמש חדש נרשם",
                "message": "משתמש חדש הצטרף למערכת.",
                "is_read": False,
                "created_at": None,
            },
            {
                "id": 2,
                "title": "בקשת עבודה חדשה",
                "message": "מועמד חדש הגיש בקשת עבודה.",
                "is_read": False,
                "created_at": None,
            },
            {
                "id": 3,
                "title": "אילוצי עובד הוגשו",
                "message": "עובד הגיש אילוצים לשבוע הבא.",
                "is_read": False,
                "created_at": None,
            },
        ],
    )

    with app.test_request_context("/"):
        session["user_id"] = 2
        session["role"] = "admin"

        result = main.inject_notifications_count()

    assert result["unread_notifications_count"] == 3
    assert len(result["header_notifications"]) == 3


def test_visitor_does_not_get_notification_context():
    app.config["TESTING"] = True

    with app.test_request_context("/"):
        session["user_id"] = 5
        session["role"] = "visitor"

        result = main.inject_notifications_count()

    assert result["unread_notifications_count"] == 0
    assert result["header_notifications"] == []


def test_notify_admins_about_new_booking(monkeypatch):
    app.config["TESTING"] = True

    captured = {"title": None, "message": None}

    def fake_create_notification_for_all_admins(title, message):
        captured["title"] = title
        captured["message"] = message

    monkeypatch.setattr(
        main,
        "create_notification_for_all_admins",
        fake_create_notification_for_all_admins,
    )

    booking_data = {
        "tour_type": "סיור משפחתי",
        "full_name": "רון כהן",
        "preferred_date": "2026-06-25",
    }

    main.notify_admins_about_new_booking(booking_data)

    assert captured["title"] == "הזמנת סיור חדשה"
    assert "רון כהן" in captured["message"]
    assert "סיור משפחתי" in captured["message"]
    assert "2026-06-25" in captured["message"]