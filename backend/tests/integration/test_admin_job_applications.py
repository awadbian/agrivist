import pytest

from backend import main


app = main.app


def _login_as_admin(client):
    with client.session_transaction() as session:
        session["user"] = "Admin"
        session["email"] = "admin@example.com"
        session["role"] = "admin"
        session["user_id"] = 1


def test_admin_dashboard_shows_job_applications(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr(main, "get_registered_users", lambda: [])
    monkeypatch.setattr(main, "get_farm_workers", lambda: [])
    monkeypatch.setattr(main, "get_all_tour_bookings", lambda: [])
    monkeypatch.setattr(main, "list_peppers", lambda: ([], []))
    monkeypatch.setattr(main, "list_admin_tours", lambda: [])
    monkeypatch.setattr(main, "get_all_payments", lambda: [])
    monkeypatch.setattr(main, "get_active_peppers_count", lambda: 0)
    monkeypatch.setattr(
        main,
        "get_combined_satisfaction_summary",
        lambda: {"average_rating": 0, "rating_count": 0},
    )

    monkeypatch.setattr(
        main,
        "get_all_job_applications",
        lambda: [
            {
                "id": 1,
                "full_name": "Test Candidate",
                "email": "candidate@example.com",
                "phone": "0501234567",
                "worked_before": True,
                "experience": "יש ניסיון בעבודה עם לקוחות.",
                "status": "pending",
                "created_at": None,
            }
        ],
    )

    with app.test_client() as client:
        _login_as_admin(client)

        response = client.get("/admin-dashboard")

    assert response.status_code == 200
    assert "ניהול מועמדים".encode("utf-8") in response.data
    assert "Test Candidate".encode("utf-8") in response.data
    assert "candidate@example.com".encode("utf-8") in response.data
    assert "ממתין".encode("utf-8") in response.data


def test_admin_can_approve_job_application(monkeypatch):
    app.config["TESTING"] = True

    approved = {"called": False}
    updated_role = {"email": None, "role": None}

    monkeypatch.setattr(
        main,
        "get_job_application_by_id",
        lambda application_id: {
            "id": application_id,
            "full_name": "Test Candidate",
            "email": "candidate@example.com",
            "phone": "0501234567",
            "worked_before": True,
            "experience": "ניסיון קודם",
            "status": "pending",
        },
    )

    monkeypatch.setattr(
        main,
        "get_user_by_email",
        lambda email: {
            "id": 10,
            "email": email,
            "full_name": "Test Candidate",
        },
    )

    def fake_update_user_role(email, role):
        updated_role["email"] = email
        updated_role["role"] = role

    def fake_approve(application_id):
        approved["called"] = True

    monkeypatch.setattr(main, "update_user_role", fake_update_user_role)
    monkeypatch.setattr(main, "approve_job_application", fake_approve)
    monkeypatch.setattr(main, "create_notification", lambda user_id, title, message: None)

    with app.test_client() as client:
        _login_as_admin(client)

        response = client.post(
            "/admin/job-applications/1/approve",
            follow_redirects=False,
        )

    assert response.status_code in (302, 303)
    assert approved["called"] is True
    assert updated_role["email"] == "candidate@example.com"
    assert updated_role["role"] == "employee"


def test_admin_can_reject_job_application(monkeypatch):
    app.config["TESTING"] = True

    rejected = {"application_id": None}

    monkeypatch.setattr(
        main,
        "get_job_application_by_id",
        lambda application_id: {
            "id": application_id,
            "full_name": "Test Candidate",
            "email": "candidate@example.com",
            "phone": "0501234567",
            "worked_before": False,
            "experience": "אין ניסיון קודם",
            "status": "pending",
        },
    )
    monkeypatch.setattr(
    main,
    "get_user_by_email",
    lambda email: {
        "id": 10,
        "email": email,
        "full_name": "Test Candidate",
    },
)

    def fake_reject(application_id):
        rejected["application_id"] = application_id

    monkeypatch.setattr(main, "reject_job_application", fake_reject)
    monkeypatch.setattr(main, "create_notification", lambda user_id, title, message: None)

    with app.test_client() as client:
        _login_as_admin(client)

        response = client.post(
            "/admin/job-applications/2/reject",
            follow_redirects=False,
        )

    assert response.status_code in (302, 303)
    assert rejected["application_id"] == 2


def test_non_admin_cannot_approve_job_application(monkeypatch):
    app.config["TESTING"] = True

    approved = {"called": False}

    def fake_approve(application_id):
        approved["called"] = True

    monkeypatch.setattr(main, "approve_job_application", fake_approve)

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["user"] = "Regular User"
            session["email"] = "user@example.com"
            session["role"] = "user"
            session["user_id"] = 2

        response = client.post(
            "/admin/job-applications/1/approve",
            follow_redirects=False,
        )

    assert response.status_code in (302, 303)
    assert approved["called"] is False