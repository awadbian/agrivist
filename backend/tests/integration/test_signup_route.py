import pytest
from backend.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_signup_get_page(client):
    response = client.get("/signup")
    assert response.status_code == 200


def test_signup_existing_email(client, monkeypatch):
    def fake_get_user_by_email(email):
        return {
            "full_name": "Existing User",
            "email": email,
            "password_hash": "hashed"
        }

    monkeypatch.setattr("backend.main.get_user_by_email", fake_get_user_by_email)

    response = client.post("/signup", data={
        "full_name": "Bian Awad",
        "email": "bian@gmail.com",
        "password": "12345678",
        "confirm_password": "12345678",
        "terms": "on"
    })

    assert response.status_code == 200
    assert "כתובת האימייל כבר קיימת במערכת.".encode("utf-8") in response.data


def test_signup_success(client, monkeypatch):
    def fake_get_user_by_email(email):
        return None

    def fake_create_user(user):
        return None

    monkeypatch.setattr("backend.main.get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr("backend.main.create_user", fake_create_user)

    monkeypatch.setattr(
    "backend.main.create_notification_for_all_admins",
    lambda title, message: None
)

    response = client.post("/signup", data={
        "full_name": "Bian Awad",
        "email": "bian@gmail.com",
        "password": "12345678",
        "confirm_password": "12345678",
        "terms": "on"
    }, follow_redirects=False)

    assert response.status_code == 302
