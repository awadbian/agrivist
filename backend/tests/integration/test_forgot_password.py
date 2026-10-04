import pytest
from backend.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_forgot_password_get_page(client):
    response = client.get("/forgot-password")
    assert response.status_code == 200


def test_forgot_password_email_not_found(client, monkeypatch):
    def fake_get_user_by_email(email):
        return None

    monkeypatch.setattr("backend.main.get_user_by_email", fake_get_user_by_email)

    response = client.post("/forgot-password", data={
        "full_name": "Bian Awad",
        "email": "bian@gmail.com",
        "new_password": "12345678",
        "confirm_password": "12345678"
    })

    assert response.status_code == 200
    assert "האימייל לא קיים במערכת.".encode("utf-8") in response.data


def test_forgot_password_name_not_match(client, monkeypatch):
    def fake_get_user_by_email(email):
        return {
            "full_name": "Someone Else",
            "email": email,
            "password_hash": "hashed"
        }

    monkeypatch.setattr("backend.main.get_user_by_email", fake_get_user_by_email)

    response = client.post("/forgot-password", data={
        "full_name": "Bian Awad",
        "email": "bian@gmail.com",
        "new_password": "12345678",
        "confirm_password": "12345678"
    })

    assert response.status_code == 200
    assert "שם המשתמש והאימייל אינם תואמים.".encode("utf-8") in response.data


def test_forgot_password_password_mismatch(client, monkeypatch):
    def fake_get_user_by_email(email):
        return {
            "full_name": "Bian Awad",
            "email": email,
            "password_hash": "hashed"
        }

    monkeypatch.setattr("backend.main.get_user_by_email", fake_get_user_by_email)

    response = client.post("/forgot-password", data={
        "full_name": "Bian Awad",
        "email": "bian@gmail.com",
        "new_password": "12345678",
        "confirm_password": "65432177"
    })

    assert response.status_code == 200
    assert "הסיסמאות אינן תואמות.".encode("utf-8") in response.data


def test_forgot_password_success(client, monkeypatch):
    def fake_get_user_by_email(email):
        return {
            "full_name": "Bian Awad",
            "email": email,
            "password_hash": "hashed"
        }

    def fake_update_user_password(email, password_hash):
        return None

    monkeypatch.setattr("backend.main.get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr("backend.main.update_user_password", fake_update_user_password)

    response = client.post("/forgot-password", data={
        "full_name": "Bian Awad",
        "email": "bian@gmail.com",
        "new_password": "12345678",
        "confirm_password": "12345678"
    })

    assert response.status_code == 200
    assert "הסיסמה עודכנה בהצלחה".encode("utf-8") in response.data
