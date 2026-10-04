import pytest

import backend.main as main


@pytest.fixture
def client():
    main.app.config["TESTING"] = True
    main.app.config["SECRET_KEY"] = "test-secret"

    with main.app.test_client() as client:
        yield client


def login_as_visitor(client):
    with client.session_transaction() as session:
        session["user"] = "Test User"
        session["email"] = "test@example.com"
        session["role"] = "visitor"
        session["user_id"] = 1


def test_home_loads_website_feedback(client, monkeypatch):
    website_feedback = [
        {
            "full_name": "ביאן",
            "rating": 5,
            "comment": "האתר נוח וברור",
        }
    ]

    website_summary = {
        "average_rating": 4.7,
        "feedback_count": 6,
    }

    captured = {}

    def fake_render_template(template_name, **context):
        captured["template"] = template_name
        captured["context"] = context
        return "OK"

    monkeypatch.setattr(main, "get_pending_tour_rating_for_user", lambda email: None)
    monkeypatch.setattr(main, "get_latest_website_feedback", lambda limit=6: website_feedback)
    monkeypatch.setattr(main, "get_website_feedback_summary", lambda: website_summary)
    monkeypatch.setattr(main, "render_template", fake_render_template)

    response = client.get("/")

    assert response.status_code == 200
    assert captured["template"] == "index.html"
    assert captured["context"]["website_feedback"] == website_feedback
    assert captured["context"]["website_feedback_summary"] == website_summary


def test_website_feedback_requires_login(client):
    response = client.get("/website-feedback", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_website_feedback_page_loads_for_logged_in_user(client, monkeypatch):
    login_as_visitor(client)

    captured = {}

    def fake_render_template(template_name, **context):
        captured["template"] = template_name
        return "OK"

    monkeypatch.setattr(main, "render_template", fake_render_template)

    response = client.get("/website-feedback")

    assert response.status_code == 200
    assert captured["template"] == "website_feedback.html"


def test_website_feedback_rejects_invalid_rating(client, monkeypatch):
    login_as_visitor(client)

    captured = {}

    def fake_render_template(template_name, **context):
        captured["template"] = template_name
        return "OK"

    monkeypatch.setattr(main, "render_template", fake_render_template)

    response = client.post(
        "/website-feedback",
        data={
            "rating": "0",
            "comment": "בדיקה",
        },
    )

    assert response.status_code == 200
    assert captured["template"] == "website_feedback.html"


def test_website_feedback_saves_valid_feedback(client, monkeypatch):
    login_as_visitor(client)

    saved_data = {}

    def fake_create_website_feedback(email, full_name, rating, comment):
        saved_data["email"] = email
        saved_data["full_name"] = full_name
        saved_data["rating"] = rating
        saved_data["comment"] = comment
        return True, "תודה! המשוב נשמר."

    monkeypatch.setattr(main, "create_website_feedback", fake_create_website_feedback)

    response = client.post(
        "/website-feedback",
        data={
            "rating": "5",
            "comment": "אתר יפה ונוח",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    assert saved_data["email"] == "test@example.com"
    assert saved_data["full_name"] == "Test User"
    assert saved_data["rating"] == 5
    assert saved_data["comment"] == "אתר יפה ונוח"


def test_admin_dashboard_loads_satisfaction_summary(client, monkeypatch):
    with client.session_transaction() as session:
        session["user"] = "Admin"
        session["email"] = "admin@example.com"
        session["role"] = "admin"
        session["user_id"] = 1

    captured = {}

    def fake_render_template(template_name, **context):
        captured["template"] = template_name
        captured["context"] = context
        return "OK"

    monkeypatch.setattr(main, "get_registered_users", lambda: [])
    monkeypatch.setattr(main, "get_farm_workers", lambda: [])
    monkeypatch.setattr(main, "get_all_tour_bookings", lambda: [])
    monkeypatch.setattr(main, "list_peppers", lambda: ([], []))
    monkeypatch.setattr(main, "list_admin_tours", lambda: [])
    monkeypatch.setattr(main, "get_all_payments", lambda: [])
    monkeypatch.setattr(main, "get_all_job_applications", lambda: [])
    monkeypatch.setattr(main, "get_active_peppers_count", lambda: 0)
    monkeypatch.setattr(
        main,
        "get_combined_satisfaction_summary",
        lambda: {
            "average_rating": 4.5,
            "rating_count": 10,
        },
    )
    monkeypatch.setattr(main, "render_template", fake_render_template)

    response = client.get("/admin-dashboard")

    assert response.status_code == 200
    assert captured["template"] == "admin/admin_dashboard.html"
    assert captured["context"]["stats"]["satisfaction_average"] == 4.5
    assert captured["context"]["stats"]["satisfaction_count"] == 10