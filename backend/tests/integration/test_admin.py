from datetime import date

from werkzeug.security import check_password_hash

from backend.main import app
from backend.service import admin_service


def _login_as(client, role):
    with client.session_transaction() as session:
        session["role"] = role
        session["user"] = f"{role.title()} User"
        session["email"] = f"{role}@example.com"


def _patch_admin_dashboard_data(monkeypatch):
    monkeypatch.setattr("backend.main.get_registered_users", lambda: [])
    monkeypatch.setattr("backend.main.get_farm_workers", lambda: [])
    monkeypatch.setattr("backend.main.get_all_tour_bookings", lambda: [])
    monkeypatch.setattr("backend.main.list_peppers", lambda: ([], {}))
    monkeypatch.setattr("backend.main.list_admin_tours", lambda: [])
    monkeypatch.setattr("backend.main.get_all_payments", lambda: [])
    monkeypatch.setattr("backend.main.get_active_peppers_count", lambda: 0)
    monkeypatch.setattr("backend.main.get_all_job_applications", lambda: [])

def test_visitor_cannot_open_add_pepper_page():
    app.config["TESTING"] = True

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["role"] = "visitor"

        response = client.get("/admin/peppers/add", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/pepper-varieties")


def test_admin_can_open_add_pepper_page():
    app.config["TESTING"] = True

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["role"] = "admin"

        response = client.get("/admin/peppers/add")

    assert response.status_code == 200


def test_admin_can_open_requested_add_pepper_url():
    app.config["TESTING"] = True

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["role"] = "admin"

        response = client.get("/admin/add-pepper")

    assert response.status_code == 200


def test_admin_dashboard_does_not_show_weekly_schedule_button(monkeypatch):
    app.config["TESTING"] = True
    _patch_admin_dashboard_data(monkeypatch)

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin-dashboard")

    assert response.status_code == 200
    assert b"Weekly Work Schedule" not in response.data


def test_admin_can_open_weekly_schedule_page():
    app.config["TESTING"] = True

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert "סידור עבודה שבועי".encode("utf-8") in response.data
    assert "ראשון–חמישי: 07:00–21:00".encode("utf-8") in response.data
    assert "שיבוץ עובדים".encode("utf-8") in response.data
    return
    assert "סידור עבודה שבועי".encode("utf-8") in response.data
    assert "כאן המנהל יוכל לבנות את סידור העבודה לשבוע הבא.".encode("utf-8") in response.data


def test_admin_weekly_schedule_excludes_saturday():
    app.config["TESTING"] = True

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b'data-day-key="saturday"' not in response.data
    assert b'data-summary-day="saturday"' not in response.data
    assert b'data-day-key="friday"' in response.data


def test_non_admin_cannot_open_weekly_schedule_page():
    app.config["TESTING"] = True

    for role in ("visitor", "employee"):
        with app.test_client() as client:
            _login_as(client, role)

            response = client.get("/admin/weekly-schedule", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")


def test_admin_weekly_schedule_includes_employee_availability_ui(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr("backend.main.load_employees_from_db", lambda: [
        {
            "name": "Worker Available",
            "email": "available@example.com",
            "role": "employee",
            "status": "לא במשמרת",
            "hourly_rate": 40,
            "shifts": [],
        },
        {
            "name": "Worker Unavailable",
            "email": "unavailable@example.com",
            "role": "employee",
            "status": "לא במשמרת",
            "hourly_rate": 40,
            "shifts": [],
        },
    ])

    def fake_get_worker_constraints(email, _week_start_date):
        if email == "available@example.com":
            return {
                "sunday": "morning",
                "monday": "all_day",
                "tuesday": "evening",
                "wednesday": "midday",
                "thursday": "all_day",
                "friday": "morning",
            }
        return {
            "sunday": "unavailable",
            "monday": "unavailable",
            "tuesday": "unavailable",
            "wednesday": "unavailable",
            "thursday": "unavailable",
            "friday": "unavailable",
        }

    monkeypatch.setattr("backend.main.get_worker_constraints", fake_get_worker_constraints)

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b"employeesAvailability" in response.data
    assert b"Worker Available" in response.data
    assert b"Worker Unavailable" in response.data
    assert b'"sunday": "morning"' in response.data
    assert b'"sunday": "unavailable"' in response.data
    assert "העובד/ת סימן/ה שאינו/ה זמין/ה למשמרת זו".encode("utf-8") in response.data
    assert "בחר/י".encode("utf-8") in response.data


def test_admin_weekly_schedule_handles_employee_without_constraints(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr("backend.main.load_employees_from_db", lambda: [
        {
            "name": "No Constraints Worker",
            "email": "no-constraints@example.com",
            "role": "employee",
            "status": "לא במשמרת",
            "hourly_rate": 40,
            "shifts": [],
        },
    ])
    monkeypatch.setattr("backend.main.get_worker_constraints", lambda _email, _week_start_date: None)

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b"No Constraints Worker" in response.data
    assert b'"constraints": {}' in response.data
    assert "לא הוגשו אילוצים".encode("utf-8") in response.data


def test_admin_can_reset_constraints_for_selected_week(monkeypatch):
    app.config["TESTING"] = True
    deleted_weeks = []

    monkeypatch.setattr(
        "backend.main.delete_worker_constraints_for_week",
        lambda week_start_date: deleted_weeks.append(week_start_date),
    )

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.post(
            "/admin/weekly-schedule/reset-constraints",
            data={"week": "2"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/weekly-schedule?week=2")
    assert len(deleted_weeks) == 1


def test_admin_can_stop_constraints_updates_for_selected_week(monkeypatch):
    app.config["TESTING"] = True
    updates = []

    monkeypatch.setattr(
        "backend.main.set_constraints_status_for_week",
        lambda week_start_date, constraints_status: updates.append(
            (week_start_date, constraints_status)
        ),
    )

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.post(
            "/admin/weekly-schedule/submission-window",
            data={"week": "2", "is_open": "0"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/weekly-schedule?week=2")
    assert len(updates) == 1
    assert updates[0][1] == "closed"


def test_admin_can_open_constraints_updates_for_selected_week(monkeypatch):
    app.config["TESTING"] = True
    opened_weeks = []

    monkeypatch.setattr("backend.main.load_weekly_schedule_status", lambda _week_start_date: "draft")
    monkeypatch.setattr(
        "backend.main.open_constraints_for_week",
        lambda week_start_date: opened_weeks.append(week_start_date),
    )

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.post(
            "/admin/weekly-schedule/submission-window",
            data={"week": "1", "is_open": "1"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/weekly-schedule?week=1")
    assert len(opened_weeks) == 1


def test_admin_cannot_reopen_constraints_after_schedule_is_published(monkeypatch):
    app.config["TESTING"] = True
    opened_weeks = []

    monkeypatch.setattr("backend.main.load_weekly_schedule_status", lambda _week_start_date: "published")
    monkeypatch.setattr(
        "backend.main.open_constraints_for_week",
        lambda week_start_date: opened_weeks.append(week_start_date),
    )

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.post(
            "/admin/weekly-schedule/submission-window",
            data={"week": "1", "is_open": "1"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/weekly-schedule?week=1")
    assert opened_weeks == []


def test_admin_weekly_schedule_shows_constraints_update_lock_button(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr("backend.main.load_employees_from_db", lambda: [])
    monkeypatch.setattr("backend.main.get_worker_constraint_submissions_for_week", lambda _week_start_date: [])
    monkeypatch.setattr("backend.main.are_constraint_updates_open", lambda _week_start_date: True)

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b'action="/admin/weekly-schedule/submission-window"' in response.data
    assert b'name="is_open" value="0"' in response.data


def test_admin_weekly_schedule_does_not_show_submission_status_button(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr(
        "backend.main.load_employees_from_db",
        lambda: [{"name": "Worker", "email": "worker@example.com"}],
    )
    monkeypatch.setattr(
        "backend.main.get_worker_constraint_submissions_for_week",
        lambda _week_start_date: [{
            "employee_email": "worker@example.com",
            "submitted_at": "2026-06-01 09:00",
            "notes": "",
        }],
    )
    monkeypatch.setattr("backend.main.are_constraint_updates_open", lambda _week_start_date: True)

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b"status-toggle-link" not in response.data
    assert b'href="#submission-status"' not in response.data
    assert "סטטוס הגשת אילוצים".encode("utf-8") in response.data
    assert "שלח/ה אילוצים".encode("utf-8") in response.data
    assert b"2026-06-01 09:00" not in response.data


def test_admin_week_selector_is_limited_to_two_weeks(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr("backend.main.load_employees_from_db", lambda: [])
    monkeypatch.setattr("backend.main.get_worker_constraint_submissions_for_week", lambda _week_start_date: [])

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule?week=4")

    assert response.status_code == 200
    assert b'value="2" selected' in response.data


def test_admin_weekly_schedule_shows_submission_status_details(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr("backend.main.load_employees_from_db", lambda: [
        {"name": "Submitted Worker", "email": "submitted@example.com", "role": "employee"},
        {"name": "Missing Worker", "email": "missing@example.com", "role": "employee"},
    ])
    monkeypatch.setattr("backend.main.get_worker_constraints", lambda _email, _week_start_date: None)
    monkeypatch.setattr("backend.main.get_worker_constraint_submissions_for_week", lambda _week_start_date: [
        {
            "employee_email": "submitted@example.com",
            "week_start_date": date(2026, 6, 7),
            "submitted_at": "2026-06-01 09:30",
            "notes": "Morning shifts",
        }
    ])

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b"Submitted Worker" in response.data
    assert b"Missing Worker" in response.data
    assert b"Morning shifts" in response.data
    assert b"not-submitted-badge" in response.data


def test_admin_can_save_weekly_schedule_draft(monkeypatch):
    app.config["TESTING"] = True
    saved = []

    def fake_save_weekly_schedule_draft_from_payload(week_start_date, assignments_payload, publish=False):
        saved.append((week_start_date, assignments_payload, publish))
        return {
            "weekly_schedule_id": 7,
            "assignments_count": 1,
            "open_constraints_week": {"week_start_date": date(2026, 6, 14)},
        }

    monkeypatch.setattr(
        "backend.main.save_weekly_schedule_draft_from_payload",
        fake_save_weekly_schedule_draft_from_payload,
    )
    payload = (
        '[{"employee_email":"worker@example.com","employee_name":"Worker",'
        '"work_date":"2026-06-07","day_name":"sunday","shift_type":"morning",'
        '"start_time":"07:00","end_time":"14:00"}]'
    )

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.post(
            "/admin/weekly-schedule/save",
            data={"week": "1", "assignments_payload": payload},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/weekly-schedule?week=1")
    assert saved[0][1] == payload
    assert saved[0][2] is True


def test_admin_can_publish_saved_weekly_schedule(monkeypatch):
    app.config["TESTING"] = True
    published_weeks = []

    monkeypatch.setattr(
        "backend.main.publish_weekly_schedule_for_employees",
        lambda week_start_date: published_weeks.append(week_start_date),
    )

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.post(
            "/admin/weekly-schedule/publish",
            data={"week": "1"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/weekly-schedule?week=1")
    assert len(published_weeks) == 1


def test_admin_weekly_schedule_replaces_editor_with_saved_table(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr("backend.main.load_employees_from_db", lambda: [])
    monkeypatch.setattr("backend.main.get_worker_constraint_submissions_for_week", lambda _week_start_date: [])
    monkeypatch.setattr("backend.main.load_weekly_schedule_status", lambda _week_start_date: "draft")
    monkeypatch.setattr("backend.main.load_saved_schedule_assignments", lambda _week_start_date: [
        {
            "employee_email": "worker@example.com",
            "employee_name": "Saved Worker",
            "day_name": "sunday",
            "shift_type": "morning",
        }
    ])

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b"has-saved-schedule" in response.data
    assert b"Saved Worker" in response.data
    assert b"saved-schedule-table" in response.data


def test_admin_weekly_schedule_empty_draft_without_assignments_shows_builder(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr("backend.main.load_employees_from_db", lambda: [])
    monkeypatch.setattr("backend.main.get_worker_constraint_submissions_for_week", lambda _week_start_date: [])
    monkeypatch.setattr("backend.main.load_weekly_schedule_status", lambda _week_start_date: "draft")
    monkeypatch.setattr("backend.main.load_saved_schedule_assignments", lambda _week_start_date: [])

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b'<main class="weekly-schedule-page">' in response.data
    assert b'id="save-schedule-form"' in response.data


def test_admin_weekly_schedule_without_saved_draft_shows_edit_builder(monkeypatch):
    app.config["TESTING"] = True

    monkeypatch.setattr("backend.main.load_weekly_schedule_status", lambda _week_start_date: "no_schedule")
    monkeypatch.setattr("backend.main.load_saved_schedule_assignments", lambda _week_start_date: [])

    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.get("/admin/weekly-schedule")

    assert response.status_code == 200
    assert b'<main class="weekly-schedule-page">' in response.data
    assert b"day-card" in response.data
    assert b"assign-btn" in response.data


def test_admin_can_reset_saved_weekly_schedule(monkeypatch):
    app.config["TESTING"] = True
    reset_weeks = []

    monkeypatch.setattr(
        "backend.main.reset_weekly_schedule_draft",
        lambda week_start_date: reset_weeks.append(week_start_date),
    )
    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.post(
            "/admin/weekly-schedule/reset",
            data={"week": "1"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/weekly-schedule?week=1")
    assert len(reset_weeks) == 1


def test_admin_reset_returns_page_to_edit_mode(monkeypatch):
    app.config["TESTING"] = True
    saved_assignments = [
        {
            "employee_email": "worker@example.com",
            "employee_name": "Saved Worker",
            "day_name": "sunday",
            "shift_type": "morning",
        }
    ]

    def fake_load_saved_schedule_assignments(_week_start_date):
        return saved_assignments

    def fake_reset_weekly_schedule_draft(_week_start_date):
        saved_assignments.clear()

    monkeypatch.setattr("backend.main.load_employees_from_db", lambda: [])
    monkeypatch.setattr("backend.main.get_worker_constraint_submissions_for_week", lambda _week_start_date: [])
    monkeypatch.setattr("backend.main.load_saved_schedule_assignments", fake_load_saved_schedule_assignments)
    monkeypatch.setattr("backend.main.reset_weekly_schedule_draft", fake_reset_weekly_schedule_draft)
    with app.test_client() as client:
        _login_as(client, "admin")

        response = client.post(
            "/admin/weekly-schedule/reset",
            data={"week": "1"},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert "הסידור אופס. שבוע הגשת האילוצים הפעיל לא השתנה.".encode("utf-8") in response.data
    assert b'<main class="weekly-schedule-page">' in response.data
    assert b"day-card" in response.data


def test_non_admin_cannot_save_weekly_schedule_draft():
    app.config["TESTING"] = True

    for role in ("visitor", "employee"):
        with app.test_client() as client:
            _login_as(client, role)

            response = client.post("/admin/weekly-schedule/save", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")


def test_employee_cannot_see_draft_weekly_schedule(monkeypatch):
    app.config["TESTING"] = True

    def fake_save_weekly_schedule_draft_from_payload(
        _week_start_date,
        _assignments_payload,
        publish=False,
    ):
        return {
            "weekly_schedule_id": 7,
            "assignments_count": 1,
            "open_constraints_week": None,
        }

    monkeypatch.setattr(
        "backend.main.save_weekly_schedule_draft_from_payload",
        fake_save_weekly_schedule_draft_from_payload,
    )

    with app.test_client() as client:
        _login_as(client, "admin")
        client.post(
            "/admin/weekly-schedule/save",
            data={
                "week": "1",
                "assignments_payload": (
                    '[{"employee_email":"employee@example.com","employee_name":"Employee User",'
                    '"work_date":"2026-06-07","day_name":"sunday","shift_type":"morning",'
                    '"start_time":"07:00","end_time":"14:00"}]'
                ),
            },
        )

        _login_as(client, "employee")
        monkeypatch.setattr(
            "backend.main.get_employee_by_email",
            lambda _email: {"name": "Employee User", "email": "employee@example.com", "shifts": []},
        )
        response = client.get("/employee-schedule")

    assert response.status_code == 200
    assert b"2026-06-07" not in response.data
    assert b"07:00" not in response.data


def test_admin_add_pepper_post_redirects_after_success(monkeypatch):
    app.config["TESTING"] = True
    saved_forms = []

    def fake_create_pepper_from_form(form_data):
        saved_forms.append(form_data)
        return 42, {}

    monkeypatch.setattr("backend.main.create_pepper_from_form", fake_create_pepper_from_form)

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["role"] = "admin"

        response = client.post(
            "/admin/add-pepper",
            data={
                "name": "Jalapeno",
                "scientific_name": "Capsicum annuum",
                "origin_country": "Mexico",
                "color": "Green",
                "scoville_level": "2,500 - 8,000",
                "heat_category": "Medium",
                "description": "Popular pepper.",
                "growing_tips": "Warm soil.",
                "image_url": "https://example.com/jalapeno.jpg",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/pepper-varieties")
    assert saved_forms[0]["name"] == "Jalapeno"
    assert saved_forms[0]["growing_tips"] == "Warm soil."
    assert "spray_info" not in saved_forms[0]


def test_admin_seed_does_nothing_when_disabled(monkeypatch):
    monkeypatch.setenv("INIT_ADMIN_ON_STARTUP", "false")

    created = admin_service.ensure_admin_user()

    assert created is False


def test_admin_seed_creates_missing_admin(monkeypatch):
    created_users = []

    monkeypatch.setenv("INIT_ADMIN_ON_STARTUP", "true")
    monkeypatch.setenv("ADMIN_FULL_NAME", "Farm Admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "AdminPass123")
    monkeypatch.setattr(admin_service, "get_user_by_email", lambda email: None)
    monkeypatch.setattr(admin_service, "create_user", lambda user: created_users.append(user))

    created = admin_service.ensure_admin_user()

    assert created is True
    assert created_users[0].full_name == "Farm Admin"
    assert created_users[0].email == "admin@example.com"
    assert created_users[0].role == "admin"
    assert check_password_hash(created_users[0].password_hash, "AdminPass123")


def test_admin_seed_promotes_existing_user(monkeypatch):
    role_updates = []
    password_updates = []

    monkeypatch.setenv("INIT_ADMIN_ON_STARTUP", "true")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "AdminPass123")
    monkeypatch.setattr(
        admin_service,
        "get_user_by_email",
        lambda email: {"email": email, "role": "visitor"},
    )
    monkeypatch.setattr(
        admin_service,
        "update_user_role",
        lambda email, role: role_updates.append((email, role)),
    )
    monkeypatch.setattr(
        admin_service,
        "update_user_password",
        lambda email, password_hash: password_updates.append((email, password_hash)),
    )

    created = admin_service.ensure_admin_user()

    assert created is False
    assert role_updates == [("admin@example.com", "admin")]
    assert password_updates[0][0] == "admin@example.com"
    assert check_password_hash(password_updates[0][1], "AdminPass123")
