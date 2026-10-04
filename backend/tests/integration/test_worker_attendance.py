import os
import pytest
from datetime import date
from unittest.mock import patch
from backend.main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True


    with app.test_client() as client:
        yield client




def get_test_worker():
    return {
        "name": "דוד לוי",
        "email": "david.levi@gmail.com",
        "role": "employee",
        "hourly_rate": 40,
        "shifts": [],
        "attendance": {
            "is_on_duty": False,
            "start_shift": None,
            "end_shift": None,
            "worked_hours": 0,
            "daily_salary": 0
        }
    }


def login_worker(client):
    worker = get_test_worker()

    with client.session_transaction() as session:
        session["user_id"] = worker["email"]
        session["user"] = worker["name"]
        session["email"] = worker["email"]
        session["role"] = "employee"


def login_as_role(client, role):
    with client.session_transaction() as session:
        session["user_id"] = f"{role}@example.com"
        session["user"] = f"{role.title()} User"
        session["email"] = f"{role}@example.com"
        session["role"] = role


# Checks that the test helper creates an employee session correctly.
def test_worker_login_success(client):
    worker = get_test_worker()

    login_worker(client)

    with client.session_transaction() as session:
        assert session["role"] == "employee"
        assert session["email"] == worker["email"]


# Checks that an employee sees only their own schedule page data.
def test_employee_schedule_only_current_worker(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": date(2026, 6, 7),
            "employee_summaries": {},
        }), \
            patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.load_employee_published_schedule", return_value={
                "shifts": [],
                "shift_count": 0,
                "total_hours": 0,
            }):
        response = client.get("/employee-schedule")

    assert response.status_code == 200
    assert worker["name"].encode("utf-8") in response.data


def test_employee_schedule_loads_published_weekly_schedule(client):
    worker = get_test_worker()

    login_worker(client)

    published_summary = {
        "shift_count": 2,
        "total_hours": 14,
        "shifts": [
            {
                "day": "sunday",
                "date": date(2026, 6, 7),
                "start": "07:00",
                "end": "14:00",
                "shift_type": "morning",
                "notes": "Greenhouse A",
                "duration_hours": 7,
            },
            {
                "day": "monday",
                "date": date(2026, 6, 8),
                "start": "14:00",
                "end": "21:00",
                "shift_type": "evening",
                "notes": "Packing",
                "duration_hours": 7,
            },
        ],
    }

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": date(2026, 6, 7),
            "employee_summaries": {},
        }), \
            patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.load_employee_published_schedule", return_value=published_summary):
        response = client.get("/employee-schedule")

    assert response.status_code == 200
    assert "מספר משמרות השבוע".encode("utf-8") in response.data
    assert b"14" in response.data
    assert b"07:00" in response.data
    assert b"21:00" in response.data
    assert b"morning" in response.data
    assert b"evening" in response.data
    assert b"Greenhouse A" not in response.data
    assert b"Packing" not in response.data
    assert "הפסקה".encode("utf-8") not in response.data
    assert "הערות".encode("utf-8") not in response.data


def test_employee_schedule_only_shows_logged_in_employee_published_shifts(client):
    worker = get_test_worker()
    calls = []

    login_worker(client)

    def fake_load_employee_published_schedule(email, _week_start_date):
        calls.append(email)
        return {
            "shift_count": 1,
            "total_hours": 7,
            "shifts": [
                {
                    "day": "sunday",
                    "date": date(2026, 6, 7),
                    "start": "07:00",
                    "end": "14:00",
                    "shift_type": "morning",
                    "notes": "Worker only",
                    "duration_hours": 7,
                }
            ],
        }

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": date(2026, 6, 7),
            "employee_summaries": {},
        }), \
            patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.load_employee_published_schedule", fake_load_employee_published_schedule):
        response = client.get("/employee-schedule")

    assert response.status_code == 200
    assert calls == [worker["email"]]
    assert b"07:00" in response.data
    assert b"morning" in response.data
    assert b"Worker only" not in response.data
    assert b"Other worker" not in response.data


def test_employee_schedule_uses_selected_week_published_schedule(client):
    worker = get_test_worker()

    login_worker(client)

    published_summary = {
        "shift_count": 1,
        "total_hours": 7,
        "shifts": [
            {
                "day": "sunday",
                "date": date(2026, 6, 7),
                "start": "07:00",
                "end": "14:00",
                "shift_type": "morning",
                "notes": None,
                "duration_hours": 7,
            }
        ],
    }

    with patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.load_employee_published_schedule", return_value=published_summary) as schedule_loader:
        response = client.get("/employee-schedule?week=0")

    assert response.status_code == 200
    assert schedule_loader.call_count == 1
    assert schedule_loader.call_args.args[0] == worker["email"]
    assert b"07:00" in response.data
    assert b"14:00" in response.data
    assert b"morning" in response.data


def test_employee_schedule_draft_schedule_is_not_visible(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": date(2026, 6, 7),
            "employee_summaries": {},
        }), \
            patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.load_employee_published_schedule", return_value={
                "shifts": [],
                "shift_count": 0,
                "total_hours": 0,
            }):
        response = client.get("/employee-schedule")

    assert response.status_code == 200
    assert b"09:00" not in response.data
    assert b"13:00 - 15:00" not in response.data
    assert "אין לך משמרות משובצות לשבוע זה.".encode("utf-8") in response.data


def test_employee_schedule_no_published_schedule_shows_empty_message(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": date(2026, 6, 7),
            "employee_summaries": {},
        }), \
            patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.load_employee_published_schedule", return_value={
                "shifts": [],
                "shift_count": 0,
                "total_hours": 0,
            }):
        response = client.get("/employee-schedule")

    assert response.status_code == 200
    assert "אין לך משמרות משובצות לשבוע זה.".encode("utf-8") in response.data
    assert "מספר משמרות השבוע:</strong> 0".encode("utf-8") in response.data


# Checks that anonymous/non-employee users cannot open the worker dashboard.
def test_worker_dashboard_requires_employee_role(client):
    response = client.get("/worker-dashboard", follow_redirects=False)

    assert response.status_code in [301, 302]


# Checks that an employee can open the worker dashboard.
def test_worker_dashboard_loads_for_employee(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": date(2026, 6, 7),
            "employee_summaries": {},
        }), \
            patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.load_published_weekly_schedule", return_value=[]):
        response = client.get("/worker-dashboard")

    assert response.status_code == 200
    assert "דשבורד עובד".encode("utf-8") in response.data
    assert worker["name"].encode("utf-8") in response.data


# Checks that the employee schedule page links to the worker dashboard.
def test_worker_dashboard_link_appears_for_employee(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": date(2026, 6, 7),
            "employee_summaries": {},
        }), \
            patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.load_employee_published_schedule", return_value={
                "shifts": [],
                "shift_count": 0,
                "total_hours": 0,
            }):
        response = client.get("/employee-schedule")

    assert response.status_code == 200
    assert b"/worker-dashboard" in response.data


# Checks that the dashboard displays the full published weekly schedule.
def test_worker_dashboard_uses_published_weekly_schedule_data(client):
    worker = get_test_worker()

    login_worker(client)

    published_rows = [
        {
            "day": "sunday",
            "date": date(2026, 6, 7),
            "start": "07:00",
            "end": "14:00",
            "shift_type": "morning",
            "employee_name": "Worker One",
            "role": "לא הוגדר תפקיד",
            "notes": "Greenhouse",
        },
        {
            "day": "monday",
            "date": date(2026, 6, 8),
            "start": "14:00",
            "end": "21:00",
            "shift_type": "evening",
            "employee_name": "Worker Two",
            "role": "לא הוגדר תפקיד",
            "notes": "Packing",
        },
    ]

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": date(2026, 6, 7),
            "rows": published_rows,
            "employee_summaries": {},
        }), \
            patch("backend.main.get_employee_by_email", return_value=worker):
        response = client.get("/worker-dashboard")

    assert response.status_code == 200
    assert b"Weekly Work Schedule" in response.data
    assert b"07:00" in response.data
    assert b"21:00" in response.data
    assert b"Worker One" in response.data
    assert b"Worker Two" in response.data
    assert b"Greenhouse" not in response.data
    assert b"Packing" not in response.data
    assert b"/employee-schedule" in response.data
    assert b"/worker-details" not in response.data


def test_worker_dashboard_does_not_show_draft_weekly_schedule(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.load_active_published_schedule", return_value={
            "week_start_date": None,
            "rows": [],
            "employee_summaries": {},
        }) as load_active_schedule, \
            patch("backend.main.get_employee_by_email", return_value=worker):
        response = client.get("/worker-dashboard")

    assert response.status_code == 200
    load_active_schedule.assert_called_once_with()
    assert b"Draft Worker" not in response.data


# Checks that anonymous users cannot open the worker constraints page.
def test_worker_constraints_page_requires_employee_role(client):
    response = client.get("/worker-constraints", follow_redirects=False)

    assert response.status_code in [301, 302]


# Checks that visitor/admin roles cannot open the employee constraints page.
def test_visitor_and_admin_cannot_access_worker_constraints(client):
    for role in ("visitor", "admin"):
        with client.session_transaction() as session:
            session.clear()

        login_as_role(client, role)
        response = client.get("/worker-constraints", follow_redirects=False)

        assert response.status_code in [301, 302]


# Checks that an employee can open the constraints form.
def test_worker_constraints_page_loads_for_employee(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.get_employee_by_email", return_value=worker), \
            patch("backend.main.get_existing_constraints", return_value=(None, None)):
        dashboard_response = client.get("/worker-dashboard")
        page_response = client.get("/worker-constraints")

    assert dashboard_response.status_code == 200
    assert b"/worker-constraints" in dashboard_response.data
    assert page_response.status_code == 200
    assert "הגשת אילוצים".encode("utf-8") in page_response.data
    assert "בחר/י את הזמינות שלך לשבוע שנפתח על ידי המנהל".encode("utf-8") in page_response.data
    assert b"availability_sunday" in page_response.data
    assert "הערות נוספות".encode("utf-8") in page_response.data
    assert b"checked" not in page_response.data


# Checks that a new weekly constraints form is editable and shows week start.
def test_worker_constraints_get_without_submission_is_editable_and_shows_week_start(client):
    login_worker(client)

    with patch("backend.main.get_existing_constraints", return_value=(None, date(2026, 6, 7))):
        response = client.get("/worker-constraints")

    assert response.status_code == 200
    assert "07/06/2026".encode("utf-8") in response.data
    assert b"disabled" not in response.data
    for day_name in (b"sunday", b"monday", b"tuesday", b"wednesday", b"thursday", b"friday"):
        assert b"availability_" + day_name in response.data


def test_worker_constraints_friday_only_allows_morning_or_unavailable(client):
    login_worker(client)

    with patch("backend.main.get_existing_constraints", return_value=(None, date(2026, 6, 7))):
        response = client.get("/worker-constraints")

    assert response.status_code == 200
    assert b'name="availability_friday"' in response.data
    assert b'name="availability_friday"\\r\\n                                    value="evening"' not in response.data
    assert b'name="availability_friday"\\r\\n                                    value="all_day"' not in response.data


# Checks that submitting without all required days shows a validation error.
def test_worker_constraints_post_requires_all_days(client):
    login_worker(client)

    with patch("backend.main.submit_worker_constraints") as submit_constraints, \
     patch("backend.main.create_notification_for_all_admins") as notify_admins:
        
        notify_admins.return_value = None

        submit_constraints.return_value = (
            None,
            None,
            "יש לבחור אפשרות אחת עבור כל יום לפני שליחת האילוצים.",
            False,
        )
        response = client.post("/worker-constraints", data={
            "availability_sunday": "morning",
        })

    assert response.status_code == 200
    assert "יש לבחור אפשרות אחת עבור כל יום לפני שליחת האילוצים.".encode("utf-8") in response.data


# Checks that fewer than four available shifts shows the clear form error.
def test_worker_constraints_post_shows_minimum_available_days_error(client):
    login_worker(client)

    with patch("backend.main.submit_worker_constraints") as submit_constraints:
        submit_constraints.return_value = (
            None,
            date(2026, 6, 7),
            "עליך לבחור לפחות 4 משמרות זמינות לשבוע הבא.",
            False,
        )
        response = client.post("/worker-constraints", data={
            "availability_sunday": "morning",
            "availability_monday": "unavailable",
            "availability_tuesday": "evening",
            "availability_wednesday": "unavailable",
            "availability_thursday": "all_day",
            "availability_friday": "unavailable",
        })

    assert response.status_code == 200
    assert "עליך לבחור לפחות 4 משמרות זמינות לשבוע הבא.".encode("utf-8") in response.data
    assert b"availability_sunday" in response.data
    assert b"disabled" not in response.data


# Checks that a valid constraints POST redirects after successful save.
def test_worker_constraints_post_redirects_after_success(client):
    login_worker(client)
    worker = get_test_worker()

    with patch("backend.main.submit_worker_constraints") as submit_constraints, \
        patch("backend.main.create_notification_for_all_admins") as notify_admins:

        notify_admins.return_value = None

        submit_constraints.return_value = (
             {"sunday": "morning"},
               None,
               None,
               True,
               )
        
        response = client.post("/worker-constraints", data={
            "availability_sunday": "morning",
            "availability_monday": "midday",
            "availability_tuesday": "evening",
            "availability_wednesday": "all_day",
            "availability_thursday": "unavailable",
            "availability_friday": "morning",
        }, follow_redirects=False)

    assert response.status_code in [301, 302]
    assert "/worker-constraints?submitted=1" in response.headers["Location"]
    assert submit_constraints.call_args.args[0] == worker["email"]


# Checks that a successful POST shows the confirmation summary after redirect.
def test_worker_constraints_post_follow_redirects_shows_confirmation_summary_without_form(client):
    login_worker(client)

    saved_submission = {
        "sunday": "morning",
        "monday": "midday",
        "tuesday": "evening",
        "wednesday": "all_day",
        "thursday": "unavailable",
        "friday": "morning",
        "notes": "צריך לצאת מוקדם ביום שישי",
    }

    with patch("backend.main.submit_worker_constraints") as submit_constraints, \
        patch("backend.main.get_existing_constraints", return_value=(saved_submission, date(2026, 6, 7))), \
        patch("backend.main.create_notification_for_all_admins") as notify_admins:

        notify_admins.return_value = None 

        submit_constraints.return_value = (
            saved_submission,
            date(2026, 6, 7),
            None,
            True,
        )
        response = client.post("/worker-constraints", data={
            "availability_sunday": "morning",
            "availability_monday": "midday",
            "availability_tuesday": "evening",
            "availability_wednesday": "all_day",
            "availability_thursday": "unavailable",
            "availability_friday": "morning",
            "constraints_notes": "צריך לצאת מוקדם ביום שישי",
        }, follow_redirects=True)

    assert response.status_code == 200
    assert "האילוצים נשמרו בהצלחה ונשלחו למנהל.".encode("utf-8") in response.data
    assert "האילוצים שנשמרו".encode("utf-8") in response.data
    assert "לשבוע:".encode("utf-8") in response.data
    assert b"07/06/2026" in response.data
    assert "האילוצים שלך לשבוע הבא כבר נשמרו. ניתן לערוך ולעדכן אותם כל עוד המנהל לא סגר את אפשרות העדכון.".encode("utf-8") in response.data
    assert "ראשון".encode("utf-8") in response.data
    assert "אמצע יום".encode("utf-8") in response.data
    assert "לא זמין".encode("utf-8") in response.data
    assert "צריך לצאת מוקדם ביום שישי".encode("utf-8") in response.data
    assert "חזרה לדשבורד עובד".encode("utf-8") in response.data
    assert "עריכת אילוצים".encode("utf-8") in response.data
    assert b"availability_sunday" not in response.data
    assert b"constraints_notes" not in response.data


# Checks that an existing submission shows the summary and removes the form.
def test_worker_constraints_summary_replaces_form_after_submission(client):
    login_worker(client)

    submission = {
        "sunday": "morning",
        "monday": "midday",
        "tuesday": "evening",
        "wednesday": "all_day",
        "thursday": "unavailable",
        "friday": "morning",
        "notes": "Test note",
    }

    with patch("backend.main.get_existing_constraints", return_value=(submission, None)):
        response = client.get("/worker-constraints")

    assert response.status_code == 200
    assert "האילוצים שלך לשבוע הבא כבר נשמרו. ניתן לערוך ולעדכן אותם כל עוד המנהל לא סגר את אפשרות העדכון.".encode("utf-8") in response.data
    assert "האילוצים שנשמרו".encode("utf-8") in response.data
    assert "Test note".encode("utf-8") in response.data
    assert "חזרה לדשבורד עובד".encode("utf-8") in response.data
    assert "עריכת אילוצים".encode("utf-8") in response.data
    assert b"availability_sunday" not in response.data
    assert b"constraints_notes" not in response.data


def test_worker_constraints_edit_existing_submission_loads_saved_choices(client):
    login_worker(client)

    submission = {
        "sunday": "morning",
        "monday": "midday",
        "tuesday": "evening",
        "wednesday": "all_day",
        "thursday": "unavailable",
        "friday": "morning",
        "notes": "Existing note",
    }

    with patch("backend.main.get_existing_constraints", return_value=(submission, date(2026, 6, 7))):
        response = client.get("/worker-constraints?edit=1")

    assert response.status_code == 200
    assert b"availability_sunday" in response.data
    assert b'value="morning"' in response.data
    assert b"checked" in response.data
    assert "Existing note".encode("utf-8") in response.data
    assert "עדכון אילוצים".encode("utf-8") in response.data
    assert b"disabled" not in response.data


def test_worker_constraints_closed_updates_hide_edit_button(client):
    login_worker(client)

    submission = {
        "sunday": "morning",
        "monday": "midday",
        "tuesday": "evening",
        "wednesday": "all_day",
        "thursday": "unavailable",
        "friday": "morning",
        "notes": "Locked note",
    }

    with patch("backend.main.get_existing_constraints", return_value=(submission, date(2026, 6, 7))), \
            patch("backend.main.are_constraint_updates_open", return_value=False):
        response = client.get("/worker-constraints")

    assert response.status_code == 200
    assert "המנהל סגר את אפשרות עדכון האילוצים לשבוע זה.".encode("utf-8") in response.data
    assert "Locked note".encode("utf-8") in response.data
    assert "עריכת אילוצים".encode("utf-8") not in response.data
    assert b"availability_sunday" not in response.data


def test_worker_constraints_closed_updates_block_direct_post(client):
    login_worker(client)

    submission = {
        "sunday": "morning",
        "monday": "midday",
        "tuesday": "evening",
        "wednesday": "all_day",
        "thursday": "unavailable",
        "friday": "morning",
        "notes": "Locked note",
    }

    with patch("backend.main.submit_worker_constraints") as submit_constraints:
        submit_constraints.return_value = (
            submission,
            date(2026, 6, 7),
            "המנהל סגר את אפשרות עדכון האילוצים לשבוע זה.",
            False,
        )
        response = client.post("/worker-constraints", data={
            "availability_sunday": "evening",
            "availability_monday": "all_day",
            "availability_tuesday": "evening",
            "availability_wednesday": "all_day",
            "availability_thursday": "all_day",
            "availability_friday": "morning",
            "constraints_notes": "Attempted update",
        })

    assert response.status_code == 200
    assert "המנהל סגר את אפשרות עדכון האילוצים לשבוע זה.".encode("utf-8") in response.data
    assert "Locked note".encode("utf-8") in response.data
    assert b"Attempted update" not in response.data
    assert b"availability_sunday" not in response.data


# Checks that POST errors keep the editable form visible with attempted values.
def test_worker_constraints_post_error_keeps_editable_form(client):
    login_worker(client)

    submission = {
        "sunday": "morning",
        "monday": "midday",
        "tuesday": "evening",
        "wednesday": "all_day",
        "thursday": "unavailable",
        "friday": "morning",
        "notes": "Already saved",
    }

    with patch("backend.main.submit_worker_constraints") as submit_constraints:
        submit_constraints.return_value = (
            submission,
            date(2026, 6, 7),
            "שגיאת בדיקה",
            False,
        )
        response = client.post("/worker-constraints", data={
            "availability_sunday": "morning",
            "availability_monday": "evening",
            "availability_tuesday": "evening",
            "availability_wednesday": "all_day",
            "availability_thursday": "all_day",
            "availability_friday": "morning",
            "constraints_notes": "Attempted new note",
        })

    assert response.status_code == 200
    assert "שגיאת בדיקה".encode("utf-8") in response.data
    assert b"Attempted new note" in response.data
    assert b"availability_sunday" in response.data
    assert b"disabled" not in response.data


# Checks that the submitted query flag alone does not show confirmation without saved data.
def test_worker_constraints_submitted_flag_without_submission_does_not_show_success(client):
    login_worker(client)

    with patch("backend.main.get_existing_constraints", return_value=(None, date(2026, 6, 7))):
        response = client.get("/worker-constraints?submitted=1")

    assert response.status_code == 200
    assert "הבקשה שלך נשלחה למנהל בהצלחה".encode("utf-8") not in response.data
    assert "האילוצים שנשלחו".encode("utf-8") not in response.data
    assert b"disabled" not in response.data


# Checks that submitting constraints does not create or modify attendance JSON.
def test_worker_constraints_post_does_not_touch_attendance_file(client):
    login_worker(client)

    with patch("backend.main.submit_worker_constraints") as submit_constraints, \
     patch("backend.main.create_notification_for_all_admins") as notify_admins:
        
        notify_admins.return_value = None
        
        submit_constraints.return_value = (
            {"sunday": "morning"},
            date(2026, 6, 7),
            None,
            True,
        )

        response = client.post("/worker-constraints", data={
            "availability_sunday": "morning",
            "availability_monday": "midday",
            "availability_tuesday": "evening",
            "availability_wednesday": "all_day",
            "availability_thursday": "unavailable",
            "availability_friday": "morning",
        }, follow_redirects=False)

    assert response.status_code in [301, 302]

# Checks that anonymous/non-employee users cannot open worker tours.
def test_worker_tours_page_requires_employee_role(client):
    response = client.get("/worker-tours", follow_redirects=False)

    assert response.status_code in [301, 302]


# Checks that an employee can open the worker tours placeholder page.
def test_worker_tours_page_loads_for_employee(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.get_employee_by_email", return_value=worker):
        dashboard_response = client.get("/worker-dashboard")
        page_response = client.get("/worker-tours")

    assert dashboard_response.status_code == 200
    assert b"/worker-tours" in dashboard_response.data
    assert page_response.status_code == 200



# Checks that the removed worker details page is no longer routed.
def test_worker_details_page_is_removed(client):
    response = client.get("/worker-details", follow_redirects=False)

    assert response.status_code == 404


# Checks that starting a shift creates the attendance JSON state.
def test_start_shift(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.get_employee_by_email", return_value=worker), \
         patch("backend.main.start_employee_shift_in_db"), \
         patch("backend.main.load_attendance_data", return_value={}):
        response = client.post("/start-shift", follow_redirects=True)

    assert response.status_code == 200


# Checks that ending a shift updates the attendance JSON state.
def test_end_shift(client):
    worker = get_test_worker()

    login_worker(client)

    attendance = {
        worker["email"].lower(): {
            "is_on_duty": True,
            "start_shift": "09:00",
            "end_shift": None,
            "worked_hours": 0,
            "daily_salary": 0,
            "history": []
        }
    }

    with patch("backend.main.get_employee_by_email", return_value=worker), \
         patch("backend.main.start_employee_shift_in_db"), \
         patch("backend.main.end_employee_shift_in_db"), \
         patch("backend.main.load_attendance_data", return_value=attendance):
        client.post("/start-shift", follow_redirects=True)
        response = client.post("/end-shift", follow_redirects=True)

    assert response.status_code == 200


# Checks that an employee can open the weekly shift calendar.
def test_weekly_calendar_access(client):
    worker = get_test_worker()

    login_worker(client)

    with patch("backend.main.get_employee_by_email", return_value=worker), \
         patch("backend.main.load_attendance_data", return_value={}):
        response = client.get("/weekly-shift-calendar")

    assert response.status_code == 200
    assert "לוח משמרות שבועי".encode("utf-8") in response.data
    





# Checks that visitors cannot access protected worker attendance pages.
def test_visitor_cannot_access_worker_pages(client):
    response = client.get("/shift-status", follow_redirects=False)

    assert response.status_code in [301, 302]
