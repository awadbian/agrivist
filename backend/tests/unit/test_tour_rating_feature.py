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

def test_home_loads_pending_review(client, monkeypatch):
    login_as_visitor(client)

    pending_review = {
        "booking_id": 10,
        "tour_type": "סיור בסיסי",
        "preferred_date": "2026-05-20",
        "preferred_time": "10:00",
    }

    captured = {}

    def fake_render_template(template_name, **context):
        captured["template"] = template_name
        captured["context"] = context
        return "OK"

    monkeypatch.setattr(main, "get_pending_tour_rating_for_user", lambda email: pending_review)
    monkeypatch.setattr(main, "get_latest_website_feedback", lambda limit=6: [])
    monkeypatch.setattr(
        main,
        "get_website_feedback_summary",
        lambda: {"average_rating": 0, "feedback_count": 0}
    )
    monkeypatch.setattr(main, "render_template", fake_render_template)

    response = client.get("/")

    assert response.status_code == 200
    assert captured["template"] == "index.html"
    assert captured["context"]["pending_review"] == pending_review

def test_tours_passes_rating_summary_to_template(client, monkeypatch):
    tour_packages = [
        {
            "id": 1,
            "title": "סיור בסיסי",
            "price": 80,
            "duration_minutes": 90,
            "max_people": 20,
            "description": "סיור בדיקה",
            "includes": "הדרכה\nטעימות",
        }
    ]

    rating_summary = {
        "סיור בסיסי": {
            "average_rating": 4.5,
            "review_count": 2,
        }
    }

    captured = {}

    def fake_render_template(template_name, **context):
        captured["template"] = template_name
        captured["context"] = context
        return "OK"

    monkeypatch.setattr(main, "list_active_tours", lambda: tour_packages)
    monkeypatch.setattr(main, "get_tour_rating_summary", lambda: rating_summary)
    monkeypatch.setattr(main, "render_template", fake_render_template)

    response = client.get("/tours")

    assert response.status_code == 200
    assert captured["template"] == "tours.html"
    assert captured["context"]["rating_summary"] == rating_summary
    assert captured["context"]["tour_packages"][0]["title"] == "סיור בסיסי"


def test_post_tour_review_requires_valid_rating(client, monkeypatch):
    login_as_visitor(client)

    pending_review = {
        "booking_id": 10,
        "tour_type": "סיור בסיסי",
        "preferred_date": "2026-05-20",
        "preferred_time": "10:00",
    }

    captured = {}

    def fake_render_template(template_name, **context):
        captured["template"] = template_name
        captured["context"] = context
        return "OK"

    monkeypatch.setattr(main, "get_pending_tour_rating_for_user", lambda email: pending_review)
    monkeypatch.setattr(main, "render_template", fake_render_template)

    response = client.post(
        "/post-tour-review",
        data={
            "rating": "0",
            "comment": "חוויה טובה",
        },
    )

    assert response.status_code == 200
    assert captured["template"] == "post_tour_review.html"
    assert captured["context"]["booking"] == pending_review


def test_post_tour_review_saves_valid_rating(client, monkeypatch):
    login_as_visitor(client)

    pending_review = {
        "booking_id": 10,
        "tour_type": "סיור בסיסי",
        "preferred_date": "2026-05-20",
        "preferred_time": "10:00",
    }

    saved_data = {}

    def fake_create_tour_rating(email, booking_id, rating, comment):
        saved_data["email"] = email
        saved_data["booking_id"] = booking_id
        saved_data["rating"] = rating
        saved_data["comment"] = comment
        return True, "תודה! הדירוג נשמר."

    monkeypatch.setattr(main, "get_pending_tour_rating_for_user", lambda email: pending_review)
    monkeypatch.setattr(main, "create_tour_rating", fake_create_tour_rating)

    response = client.post(
        "/post-tour-review",
        data={
            "rating": "5",
            "comment": "היה מצוין",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    assert saved_data["email"] == "test@example.com"
    assert saved_data["booking_id"] == 10
    assert saved_data["rating"] == 5
    assert saved_data["comment"] == "היה מצוין"


def test_post_tour_review_redirects_if_no_pending_review(client, monkeypatch):
    login_as_visitor(client)

    monkeypatch.setattr(main, "get_pending_tour_rating_for_user", lambda email: None)

    response = client.get("/post-tour-review", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"