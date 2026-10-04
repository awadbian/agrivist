from datetime import date

from backend.service import worker_constraints_service as service


def _valid_constraints_form():
    return {
        "availability_sunday": "morning",
        "availability_monday": "evening",
        "availability_tuesday": "all_day",
        "availability_wednesday": "morning",
        "availability_thursday": "unavailable",
        "availability_friday": "morning",
        "constraints_notes": "Can work mornings.",
    }


def test_employee_can_submit_constraints_for_active_open_week(monkeypatch):
    saved = []

    monkeypatch.setattr(
        service,
        "get_existing_constraints",
        lambda employee_email, today=None: (None, date(2026, 6, 7)),
    )
    monkeypatch.setattr(service, "is_published_schedule_week", lambda _week_start_date: False)
    monkeypatch.setattr(service, "are_constraint_updates_open", lambda _week_start_date: True)
    monkeypatch.setattr(service, "get_closed_constraint_days", lambda _week_start_date: {"saturday"})

    def fake_save_worker_constraints(employee_email, week_start_date, availability, notes):
        saved.append((employee_email, week_start_date, availability, notes))

    monkeypatch.setattr(service, "save_worker_constraints", fake_save_worker_constraints)
    monkeypatch.setattr(
        service,
        "get_worker_constraints",
        lambda employee_email, week_start_date: {
            "employee_email": employee_email,
            "week_start_date": week_start_date,
            "notes": "Can work mornings.",
            "sunday": "morning",
            "monday": "evening",
            "tuesday": "all_day",
            "wednesday": "morning",
            "thursday": "unavailable",
            "friday": "morning",
        },
    )

    submission, week_start_date, error, was_saved = service.submit_worker_constraints(
        "worker@example.com",
        _valid_constraints_form(),
    )

    assert error is None
    assert was_saved is True
    assert week_start_date == date(2026, 6, 7)
    assert submission["employee_email"] == "worker@example.com"
    assert saved == [(
        "worker@example.com",
        date(2026, 6, 7),
        {
            "sunday": "morning",
            "monday": "evening",
            "tuesday": "all_day",
            "wednesday": "morning",
            "thursday": "unavailable",
            "friday": "morning",
        },
        "Can work mornings.",
    )]


def test_employee_cannot_submit_constraints_when_manager_closed_window(monkeypatch):
    saved = []
    existing_submission = {
        "employee_email": "worker@example.com",
        "week_start_date": date(2026, 6, 7),
        "sunday": "morning",
    }

    monkeypatch.setattr(
        service,
        "get_existing_constraints",
        lambda employee_email, today=None: (existing_submission, date(2026, 6, 7)),
    )
    monkeypatch.setattr(service, "is_published_schedule_week", lambda _week_start_date: False)
    monkeypatch.setattr(service, "are_constraint_updates_open", lambda _week_start_date: False)
    monkeypatch.setattr(
        service,
        "save_worker_constraints",
        lambda *args: saved.append(args),
    )

    submission, week_start_date, error, was_saved = service.submit_worker_constraints(
        "worker@example.com",
        _valid_constraints_form(),
    )

    assert submission == existing_submission
    assert week_start_date == date(2026, 6, 7)
    assert error == service.CONSTRAINT_UPDATES_CLOSED_MESSAGE
    assert was_saved is False
    assert saved == []


def test_employee_cannot_submit_constraints_after_schedule_is_published(monkeypatch):
    saved = []

    monkeypatch.setattr(
        service,
        "get_existing_constraints",
        lambda employee_email, today=None: (None, date(2026, 6, 7)),
    )
    monkeypatch.setattr(service, "is_published_schedule_week", lambda _week_start_date: True)
    monkeypatch.setattr(
        service,
        "save_worker_constraints",
        lambda *args: saved.append(args),
    )

    submission, week_start_date, error, was_saved = service.submit_worker_constraints(
        "worker@example.com",
        _valid_constraints_form(),
    )

    assert submission is None
    assert week_start_date == date(2026, 6, 7)
    assert error == service.PUBLISHED_WEEK_CONSTRAINTS_CLOSED_MESSAGE
    assert was_saved is False
    assert saved == []
