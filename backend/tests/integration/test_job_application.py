import pytest
from unittest.mock import patch
from backend.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as test_client:
        yield test_client


# ─── עוזר: הגדרת session ───────────────────────────────────────────────────

def set_session(client, role, user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user"] = "Test User"
        sess["email"] = "test@test.com"
        sess["role"] = role


# ─── בדיקות GET ────────────────────────────────────────────────────────────

class TestJobApplicationGet:

    def test_visitor_can_see_form(self, client):
        """Visitor can access the job application form"""
        set_session(client, "visitor")
        response = client.get("/job-application")
        assert response.status_code == 200

    def test_guest_redirected_to_login(self, client):
        """Unauthenticated user is redirected to login"""
        response = client.get("/job-application")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_employee_redirected_to_worker_dashboard(self, client):
        """Employee is redirected to worker dashboard"""
        set_session(client, "employee")
        response = client.get("/job-application")
        assert response.status_code == 302
        assert "worker-dashboard" in response.headers["Location"]

    def test_admin_redirected_to_admin_dashboard(self, client):
        """Admin is redirected to admin dashboard"""
        set_session(client, "admin")
        response = client.get("/job-application")
        assert response.status_code == 302
        assert "admin-dashboard" in response.headers["Location"]


# ─── בדיקות POST ───────────────────────────────────────────────────────────

class TestJobApplicationPost:

    @patch("backend.main.create_job_application")
    @patch("backend.main.create_notification_for_all_admins")
    def test_visitor_can_submit_form(self, mock_notify, mock_create, client):
        """Visitor can submit the job application form"""
        set_session(client, "visitor")
        response = client.post("/job-application", data={
            "full_name": "Test User",
            "email": "test@test.com",
            "phone": "0501234567",
            "worked_before": "0",
            "experience": "Some experience"
        })
        assert mock_create.called
        assert response.status_code == 302

    @patch("backend.main.create_job_application")
    def test_employee_cannot_submit_form(self, mock_create, client):
        """Employee cannot submit the job application form"""
        set_session(client, "employee")
        response = client.post("/job-application", data={
            "full_name": "Worker",
            "email": "worker@test.com",
            "phone": "0501234567",
            "worked_before": "1",
            "experience": "Some experience"
        })
        assert not mock_create.called
        assert response.status_code == 302
        assert "worker-dashboard" in response.headers["Location"]

    @patch("backend.main.create_job_application")
    def test_admin_cannot_submit_form(self, mock_create, client):
        """Admin cannot submit the job application form"""
        set_session(client, "admin")
        response = client.post("/job-application", data={
            "full_name": "Admin",
            "email": "admin@test.com",
            "phone": "0501234567",
            "worked_before": "0",
            "experience": "Some experience"
        })
        assert not mock_create.called
        assert response.status_code == 302
        assert "admin-dashboard" in response.headers["Location"]
        