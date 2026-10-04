from datetime import date

from backend.service import weekly_schedule_service as service


def test_normalize_week_offset_supports_two_weeks_ahead():
    assert service.normalize_week_offset("1") == 1
    assert service.normalize_week_offset("2") == 2
    assert service.normalize_week_offset("3") == 2


def test_submission_status_separates_submitted_and_missing_employees():
    employees = [
        {"name": "Submitted Worker", "email": "submitted@example.com"},
        {"name": "Missing Worker", "email": "missing@example.com"},
    ]
    submissions = {
        "submitted@example.com": {
            "submitted_at": "2026-06-01 10:00",
            "notes": "Available mornings",
        }
    }

    statuses = service.build_submission_status(employees, submissions)

    assert statuses[0]["submitted"] is True
    assert statuses[0]["notes"] == "Available mornings"
    assert statuses[1]["submitted"] is False


def test_admin_week_days_exclude_saturday_and_friday_evening():
    week_days = service.build_week_days(date(2026, 6, 7))
    day_keys = [day["key"] for day in week_days]
    friday = next(day for day in week_days if day["key"] == "friday")

    assert day_keys == ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]
    assert [shift["type"] for shift in friday["shifts"]] == ["morning"]


def test_saved_schedule_table_excludes_saturday_and_friday_evening():
    week_days = service.build_week_days(date(2026, 6, 7))
    table = service.build_saved_schedule_table(
        week_days,
        [
            {
                "employee_email": "worker@example.com",
                "employee_name": "Worker",
                "day_name": "sunday",
                "shift_type": "morning",
            },
            {
                "employee_email": "ignored@example.com",
                "employee_name": "Ignored",
                "day_name": "saturday",
                "shift_type": "morning",
            },
            {
                "employee_email": "ignored@example.com",
                "employee_name": "Ignored",
                "day_name": "friday",
                "shift_type": "evening",
            },
        ],
    )
    friday_evening_cell = table["rows"][1]["cells"][-1]

    assert [day["key"] for day in table["days"]] == [
        "sunday", "monday", "tuesday", "wednesday", "thursday", "friday",
    ]
    assert friday_evening_cell["has_shift"] is False


def test_employee_schedule_summary_uses_real_assignment_fields():
    summary = service.build_employee_schedule_summary([
        {
            "work_date": date(2026, 6, 7),
            "day_name": "sunday",
            "shift_type": "morning",
            "start_time": "07:00",
            "end_time": "14:00",
            "notes": "Greenhouse A",
        },
        {
            "work_date": date(2026, 6, 8),
            "day_name": "monday",
            "shift_type": "evening",
            "start_time": "14:00",
            "end_time": "21:00",
            "notes": None,
        },
    ])

    assert summary["shift_count"] == 2
    assert summary["total_hours"] == 14
    assert summary["shifts"][0]["date"] == date(2026, 6, 7)
    assert summary["shifts"][0]["shift_type"] == "morning"
    assert summary["shifts"][0]["notes"] == "Greenhouse A"


def test_employee_schedule_summary_handles_missing_times_without_fake_hours():
    summary = service.build_employee_schedule_summary([
        {
            "work_date": date(2026, 6, 7),
            "day_name": "sunday",
            "shift_type": "morning",
            "start_time": None,
            "end_time": None,
            "notes": None,
        }
    ])

    assert summary["shift_count"] == 1
    assert summary["total_hours"] == 0
    assert summary["shifts"][0]["duration_hours"] == 0


def test_published_weekly_schedule_rows_include_all_employee_assignments():
    rows = service.build_published_weekly_schedule_rows([
        {
            "work_date": date(2026, 6, 7),
            "day_name": "sunday",
            "shift_type": "morning",
            "start_time": "07:00",
            "end_time": "14:00",
            "employee_name": "Worker One",
            "employee_email": "one@example.com",
            "notes": "Greenhouse",
        },
        {
            "work_date": date(2026, 6, 8),
            "day_name": "monday",
            "shift_type": "evening",
            "start_time": "14:00",
            "end_time": "21:00",
            "employee_name": "Worker Two",
            "employee_email": "two@example.com",
            "notes": None,
        },
    ])

    assert len(rows) == 2
    assert rows[0]["employee_name"] == "Worker One"
    assert rows[0]["shift_type"] == "morning"
    assert rows[0]["notes"] == "Greenhouse"
    assert rows[0]["role"] == "לא הוגדר תפקיד"
    assert rows[1]["employee_name"] == "Worker Two"


def test_load_published_weekly_schedule_filters_to_published_status(monkeypatch):
    calls = []

    def fake_get_weekly_schedule_assignments(week_start_date, status=None):
        calls.append((week_start_date, status))
        return []

    monkeypatch.setattr(
        service,
        "get_weekly_schedule_assignments",
        fake_get_weekly_schedule_assignments,
    )

    rows = service.load_published_weekly_schedule(date(2026, 6, 7))

    assert rows == []
    assert calls == [(date(2026, 6, 7), "published")]


def test_normalize_schedule_assignments_contains_required_saved_fields():
    assignments = service.normalize_schedule_assignments([
        {
            "employee_email": "WORKER@EXAMPLE.COM",
            "employee_name": "Worker Name",
            "work_date": "2026-06-07",
            "day_name": "sunday",
            "shift_type": "morning",
            "start_time": "07:00",
            "end_time": "14:00",
        }
    ])

    assert assignments == [
        {
            "employee_email": "worker@example.com",
            "employee_name": "Worker Name",
            "work_date": date(2026, 6, 7),
            "day_name": "sunday",
            "shift_type": "morning",
            "start_time": "07:00",
            "end_time": "14:00",
            "notes": None,
        }
    ]


def test_save_weekly_schedule_draft_from_payload_calls_repository(monkeypatch):
    saved = []

    def fake_save_weekly_schedule_draft(week_start_date, assignments, publish=False):
        saved.append((week_start_date, assignments, publish))
        return 44

    monkeypatch.setattr(service, "save_weekly_schedule_draft", fake_save_weekly_schedule_draft)

    result = service.save_weekly_schedule_draft_from_payload(
        date(2026, 6, 7),
        """
        [
          {
            "employee_email": "worker@example.com",
            "employee_name": "Worker",
            "work_date": "2026-06-07",
            "day_name": "sunday",
            "shift_type": "morning",
            "start_time": "07:00",
            "end_time": "14:00"
          }
        ]
        """,
    )

    assert result == {
        "weekly_schedule_id": 44,
        "assignments_count": 1,
        "open_constraints_week": None,
    }
    assert saved[0][0] == date(2026, 6, 7)
    assert saved[0][1][0]["employee_email"] == "worker@example.com"
    assert saved[0][2] is False


def test_admin_save_publish_closes_current_week_and_opens_next_constraints_week(monkeypatch):
    saved = []
    status_updates = []
    opened_weeks = []

    def fake_save_weekly_schedule_draft(week_start_date, assignments, publish=False):
        saved.append((week_start_date, assignments, publish))
        return 55

    def fake_set_constraints_status_for_week(week_start_date, constraints_status):
        status_updates.append((week_start_date, constraints_status))

    def fake_open_constraints_for_week(week_start_date):
        opened_weeks.append(week_start_date)
        return {
            "week_start_date": week_start_date,
            "constraints_status": "open",
            "status": "draft",
        }

    monkeypatch.setattr(service, "save_weekly_schedule_draft", fake_save_weekly_schedule_draft)
    monkeypatch.setattr(service, "set_constraints_status_for_week", fake_set_constraints_status_for_week)
    monkeypatch.setattr(service, "open_constraints_for_week", fake_open_constraints_for_week)

    result = service.save_weekly_schedule_draft_from_payload(
        date(2026, 6, 7),
        """
        [
          {
            "employee_email": "worker@example.com",
            "employee_name": "Worker",
            "work_date": "2026-06-07",
            "day_name": "sunday",
            "shift_type": "morning",
            "start_time": "07:00",
            "end_time": "14:00"
          }
        ]
        """,
        publish=True,
    )

    assert saved[0][0] == date(2026, 6, 7)
    assert saved[0][2] is True
    assert status_updates == [(date(2026, 6, 7), "closed")]
    assert opened_weeks == [date(2026, 6, 14)]
    assert result == {
        "weekly_schedule_id": 55,
        "assignments_count": 1,
        "open_constraints_week": {
            "week_start_date": date(2026, 6, 14),
            "constraints_status": "open",
            "status": "draft",
        },
    }
