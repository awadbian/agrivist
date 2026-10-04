import pytest
import backend.main as main


@pytest.fixture
def client():
    main.app.config["TESTING"] = True
    main.app.config["SECRET_KEY"] = "test-secret-key"

    with main.app.test_client() as client:
        yield client


def login_session(client):
    with client.session_transaction() as session:
        session["user"] = "Test User"
        session["email"] = "test@example.com"
        session["role"] = "visitor"


# -----------------------------
# Unit Tests - Profile behavior
# -----------------------------

def test_profile_redirects_to_login_when_user_not_logged_in(client):
    response = client.get("/profile")

    assert response.status_code == 302
    assert "/login" in response.location


def test_delete_account_redirects_to_login_when_user_not_logged_in(client):
    response = client.post("/delete-account")

    assert response.status_code == 302
    assert "/login" in response.location


def test_profile_post_updates_user_profile(monkeypatch, client):
    login_session(client)

    updated_data = {}

    def fake_get_user_by_email(email):
        return {
            "full_name": "Old Name",
            "email": email,
            "phone": "",
            "city": "",
            "about": "",
            "role": "visitor"
        }

    def fake_update_user_profile(email, full_name, phone, city, about):
        updated_data["email"] = email
        updated_data["full_name"] = full_name
        updated_data["phone"] = phone
        updated_data["city"] = city
        updated_data["about"] = about

    monkeypatch.setattr(main, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(main, "update_user_profile", fake_update_user_profile)

    response = client.post("/profile", data={
        "full_name": "New Name",
        "phone": "0501234567",
        "city": "Haifa",
        "about": "I like agriculture"
    })

    assert response.status_code == 302
    assert "/profile" in response.location

    assert updated_data["email"] == "test@example.com"
    assert updated_data["full_name"] == "New Name"
    assert updated_data["phone"] == "0501234567"
    assert updated_data["city"] == "Haifa"
    assert updated_data["about"] == "I like agriculture"


def test_profile_post_updates_session_name(monkeypatch, client):
    login_session(client)

    def fake_get_user_by_email(email):
        return {
            "full_name": "Old Name",
            "email": email,
            "phone": "",
            "city": "",
            "about": "",
            "role": "visitor"
        }

    def fake_update_user_profile(email, full_name, phone, city, about):
        pass

    monkeypatch.setattr(main, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(main, "update_user_profile", fake_update_user_profile)

    client.post("/profile", data={
        "full_name": "Updated User",
        "phone": "0522222222",
        "city": "Tel Aviv",
        "about": "Hello"
    })

    with client.session_transaction() as session:
        assert session["user"] == "Updated User"


# -----------------------------
# Integration Tests - Flask routes
# -----------------------------

def test_profile_get_displays_user_data(monkeypatch, client):
    login_session(client)

    def fake_get_user_by_email(email):
        return {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "0501234567",
            "city": "Jerusalem",
            "about": "Agriculture lover",
            "role": "visitor"
        }

    monkeypatch.setattr(main, "get_user_by_email", fake_get_user_by_email)

    response = client.get("/profile")

    assert response.status_code == 200
    assert "Test User".encode("utf-8") in response.data
    assert "test@example.com".encode("utf-8") in response.data
    assert "0501234567".encode("utf-8") in response.data
    assert "Jerusalem".encode("utf-8") in response.data
    assert "Agriculture lover".encode("utf-8") in response.data


def test_delete_account_deletes_user_and_clears_session(monkeypatch, client):
    login_session(client)

    deleted = {}

    def fake_delete_user_by_email(email):
        deleted["email"] = email

    monkeypatch.setattr(main, "delete_user_by_email", fake_delete_user_by_email)

    response = client.post("/delete-account")

    assert response.status_code == 302
    assert "/" in response.location

    assert deleted["email"] == "test@example.com"

    with client.session_transaction() as session:
        assert "user" not in session
        assert "email" not in session
        assert "role" not in session


def test_profile_page_contains_save_button_and_delete_button(monkeypatch, client):
    login_session(client)

    def fake_get_user_by_email(email):
        return {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "",
            "city": "",
            "about": "",
            "role": "visitor"
        }

    monkeypatch.setattr(main, "get_user_by_email", fake_get_user_by_email)

    response = client.get("/profile")

    assert response.status_code == 200
    assert "שמור שינויים".encode("utf-8") in response.data
    assert "מחק חשבון לצמיתות".encode("utf-8") in response.data


def test_profile_page_contains_password_change_link(monkeypatch, client):
    login_session(client)

    def fake_get_user_by_email(email):
        return {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "",
            "city": "",
            "about": "",
            "role": "visitor"
        }

    monkeypatch.setattr(main, "get_user_by_email", fake_get_user_by_email)

    response = client.get("/profile")

    assert response.status_code == 200
    assert b"/forgot-password" in response.data
