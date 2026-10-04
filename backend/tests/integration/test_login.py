import pytest
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from backend.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("backend.main.get_employee_from_db", return_value=None)
@patch("backend.main.get_user_by_email")
def test_login_email_not_found(mock_get_user, mock_get_employee, client):
    mock_get_user.return_value = None

    response = client.post("/login", data={
        "email": "test@test.com",
        "password": "1234"
    })

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert "user" not in session


@patch("backend.main.get_employee_from_db", return_value=None)
@patch("backend.main.get_user_by_email")
def test_login_wrong_password(mock_get_user, mock_get_employee, client):
    mock_get_user.return_value = {
        "id": 1,
        "full_name": "Test User",
        "email": "test@test.com",
        "password_hash": generate_password_hash("correct123"),
        "role": "visitor"
    }

    response = client.post("/login", data={
        "email": "test@test.com",
        "password": "wrong123"
    })

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert "user" not in session


@patch("backend.main.get_employee_from_db", return_value=None)
@patch("backend.main.get_user_by_email")
def test_login_success(mock_get_user, mock_get_employee, client):
    mock_get_user.return_value = {
        "id": 1,
        "full_name": "Test User",
        "email": "test@test.com",
        "password_hash": generate_password_hash("correct123"),
        "role": "visitor"
    }

    response = client.post("/login", data={
        "email": "test@test.com",
        "password": "correct123"
    }, follow_redirects=False)

    assert response.status_code == 302