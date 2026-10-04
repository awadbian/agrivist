import json
from datetime import date, datetime, timedelta

from backend.data_access.employee_schedule_settings_repository import get_closed_days_for_week
from backend.data_access.weekly_schedule_repository import (
    CONSTRAINTS_STATUS_CLOSED,
    CONSTRAINTS_STATUS_OPEN,
    delete_weekly_schedule_draft,
    get_active_published_assignments,
    get_active_published_week,
    get_open_constraints_week,
    get_published_assignments_for_week,
    get_published_assignments_for_employee,
    get_published_assignments_for_employee_between,
    get_weekly_schedule_week,
    get_weekly_schedule_assignments,
    open_constraints_for_week,
    publish_weekly_schedule,
    save_weekly_schedule_draft,
    set_constraints_status_for_week,
)

WEEK_DAYS = (
    ("sunday", "ראשון"),
    ("monday", "שני"),
    ("tuesday", "שלישי"),
    ("wednesday", "רביעי"),
    ("thursday", "חמישי"),
    ("friday", "שישי"),
    ("saturday", "שבת"),
)
MAX_WEEK_OFFSET = 2
WORK_WEEK_END_OFFSET_DAYS = 5
VALID_SHIFT_TYPES = {"morning", "evening", "full_day", "all_day", "day_off", "not_available", "unavailable"}
SHIFT_DEFINITIONS = {
    "morning": {
        "name": "בוקר",
        "hours": "07:00-14:00",
        "start_time": "07:00",
        "end_time": "14:00",
    },
    "evening": {
        "name": "ערב",
        "hours": "14:00-21:00",
        "start_time": "14:00",
        "end_time": "21:00",
    },
}


def current_week_sunday(today=None):
    current_date = today or date.today()
    return current_date - timedelta(days=(current_date.weekday() + 1) % 7)


def normalize_week_offset(raw_offset):
    try:
        week_offset = int(raw_offset)
    except (TypeError, ValueError):
        return 1

    if week_offset < 1:
        return 1
    if week_offset > MAX_WEEK_OFFSET:
        return MAX_WEEK_OFFSET
    return week_offset


def week_start_for_offset(week_offset, today=None):
    return current_week_sunday(today) + timedelta(weeks=week_offset)


def build_week_options(selected_week_offset, today=None):
    base_sunday = current_week_sunday(today)
    options = []

    for offset in range(1, MAX_WEEK_OFFSET + 1):
        start = base_sunday + timedelta(weeks=offset)
        options.append({
            "offset": offset,
            "label": f"שבוע {offset}",
            "start": start,
            "end": start + timedelta(days=WORK_WEEK_END_OFFSET_DAYS),
            "is_selected": offset == selected_week_offset,
        })

    return options


def load_closed_day_keys(week_start_date):
    closed_keys = set()

    try:
        for row in get_closed_days_for_week(week_start_date):
            if row.get("is_closed"):
                closed_keys.add(row.get("day_name"))
    except Exception as exc:
        print(f"Warning: failed to load closed days for weekly schedule: {exc}")

    return closed_keys


def build_week_days(week_start_date, closed_day_keys=None):
    closed_day_keys = set(closed_day_keys or ())
    week_days = []

    for day_index, (day_key, day_name) in enumerate(WEEK_DAYS):
        if day_key == "saturday":
            continue

        day_date = week_start_date + timedelta(days=day_index)
        is_friday = day_key == "friday"
        is_closed = day_key in closed_day_keys
        shifts = []

        if not is_closed:
            shifts.append({
                "name": SHIFT_DEFINITIONS["morning"]["name"],
                "hours": SHIFT_DEFINITIONS["morning"]["hours"],
                "type": "morning",
                "start_time": SHIFT_DEFINITIONS["morning"]["start_time"],
                "end_time": SHIFT_DEFINITIONS["morning"]["end_time"],
            })

            if not is_friday:
                shifts.append({
                    "name": SHIFT_DEFINITIONS["evening"]["name"],
                    "hours": SHIFT_DEFINITIONS["evening"]["hours"],
                    "type": "evening",
                    "start_time": SHIFT_DEFINITIONS["evening"]["start_time"],
                    "end_time": SHIFT_DEFINITIONS["evening"]["end_time"],
                })

        week_days.append({
            "key": day_key,
            "name": day_name,
            "date": day_date,
            "is_closed": is_closed,
            "shifts": shifts,
        })

    return week_days


def build_week_days(week_start_date, closed_day_keys=None):
    closed_day_keys = set(closed_day_keys or ())
    week_days = []

    for day_index, (day_key, day_name) in enumerate(WEEK_DAYS):
        if day_key == "saturday":
            continue

        day_date = week_start_date + timedelta(days=day_index)
        is_closed = day_key in closed_day_keys
        shifts = []

        if not is_closed:
            shifts.append({"type": "morning", **SHIFT_DEFINITIONS["morning"]})

            if day_key != "friday":
                shifts.append({"type": "evening", **SHIFT_DEFINITIONS["evening"]})

        week_days.append({
            "key": day_key,
            "name": day_name,
            "date": day_date,
            "is_closed": is_closed,
            "shifts": shifts,
        })

    return week_days


def build_submission_status(employees, submissions_by_email):
    statuses = []

    for employee in employees:
        email = employee.get("email", "")
        submission = submissions_by_email.get(email.lower())
        statuses.append({
            "name": employee.get("name", ""),
            "email": email,
            "submitted": bool(submission),
            "submitted_at": submission.get("submitted_at") if submission else None,
            "notes": submission.get("notes") if submission else "",
        })

    return statuses


def load_saved_schedule_assignments(week_start_date):
    try:
        return get_weekly_schedule_assignments(week_start_date)
    except Exception as exc:
        print(f"Warning: failed to load saved weekly schedule: {exc}")
        return []


def load_weekly_schedule_status(week_start_date):
    try:
        week = get_weekly_schedule_week(week_start_date)
    except Exception as exc:
        print(f"Warning: failed to load weekly schedule status: {exc}")
        week = None

    return week.get("status") if week else "no_schedule"


def load_weekly_constraints_status(week_start_date):
    try:
        week = get_weekly_schedule_week(week_start_date)
    except Exception as exc:
        print(f"Warning: failed to load weekly constraints status: {exc}")
        week = None

    return week.get("constraints_status") if week else CONSTRAINTS_STATUS_CLOSED


def next_constraints_week_after_publish(published_week_start_date):
    return published_week_start_date + timedelta(days=7)


def advance_constraints_window_after_publish(published_week_start_date):
    open_week_start_date = next_constraints_week_after_publish(published_week_start_date)
    set_constraints_status_for_week(published_week_start_date, CONSTRAINTS_STATUS_CLOSED)
    open_week = open_constraints_for_week(open_week_start_date)
    return open_week


def load_active_constraints_week_context():
    try:
        return get_open_constraints_week()
    except Exception as exc:
        print(f"Warning: failed to load active constraints week context: {exc}")
        return None


def build_saved_schedule_table(week_days, saved_assignments):
    assignments_by_key = {}

    for assignment in saved_assignments:
        key = (assignment.get("day_name"), assignment.get("shift_type"))
        employee_label = assignment.get("employee_name") or assignment.get("employee_email")
        assignments_by_key.setdefault(key, []).append(employee_label or "לא שובץ עובד")

    rows = []
    for shift_type in ("morning", "evening"):
        shift = SHIFT_DEFINITIONS[shift_type]
        cells = []

        for day in week_days:
            has_shift = any(day_shift["type"] == shift_type for day_shift in day["shifts"])
            employees = assignments_by_key.get((day["key"], shift_type), [])
            cells.append({
                "day_key": day["key"],
                "has_shift": has_shift,
                "hours": shift["hours"] if has_shift else "",
                "employees": employees or ["לא שובץ עובד"],
            })

        rows.append({
            "shift_type": shift_type,
            "shift_name": shift["name"],
            "hours": shift["hours"],
            "cells": cells,
        })

    return {"days": week_days, "rows": rows}


def _parse_shift_time(time_text):
    try:
        return datetime.strptime(time_text, "%H:%M").time()
    except (TypeError, ValueError):
        return None


def _assignment_duration_hours(assignment):
    start_time = _parse_shift_time(assignment.get("start_time"))
    end_time = _parse_shift_time(assignment.get("end_time"))
    if not start_time or not end_time:
        return 0

    start_datetime = datetime.combine(date.today(), start_time)
    end_datetime = datetime.combine(date.today(), end_time)
    if end_datetime <= start_datetime:
        return 0

    return round((end_datetime - start_datetime).seconds / 3600, 2)


def build_employee_schedule_summary(assignments):
    shifts = []
    total_hours = 0

    for assignment in assignments or []:
        duration_hours = _assignment_duration_hours(assignment)
        total_hours += duration_hours
        shifts.append({
            "day": assignment.get("day_name"),
            "date": assignment.get("work_date"),
            "start": assignment.get("start_time"),
            "end": assignment.get("end_time"),
            "shift_type": assignment.get("shift_type"),
            "notes": assignment.get("notes"),
            "duration_hours": duration_hours,
        })

    return {
        "shifts": shifts,
        "shift_count": len(shifts),
        "total_hours": round(total_hours, 2),
    }


def load_employee_published_schedule(employee_email, week_start_date):
    assignments = get_published_assignments_for_employee(employee_email, week_start_date)
    return build_employee_schedule_summary(assignments)


def month_date_range(reference_date):
    month_start = reference_date.replace(day=1)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    return month_start, next_month_start - timedelta(days=1)


def load_employee_monthly_published_schedule(employee_email, reference_date):
    month_start, month_end = month_date_range(reference_date)
    assignments = get_published_assignments_for_employee_between(
        employee_email,
        month_start,
        month_end,
    )
    return build_employee_schedule_summary(assignments)


def build_employee_schedule_summaries_by_email(assignments):
    assignments_by_email = {}

    for assignment in assignments or []:
        email = (assignment.get("employee_email") or "").lower()
        assignments_by_email.setdefault(email, []).append(assignment)

    return {
        email: build_employee_schedule_summary(employee_assignments)
        for email, employee_assignments in assignments_by_email.items()
    }


def load_published_employee_schedules_for_week(week_start_date):
    assignments = get_published_assignments_for_week(week_start_date)
    return build_employee_schedule_summaries_by_email(assignments)


def load_active_published_schedule():
    try:
        week = get_active_published_week()
    except Exception as exc:
        print(f"Warning: failed to load active published weekly schedule: {exc}")
        week = None

    if not week:
        return {
            "week_start_date": None,
            "assignments": [],
            "rows": [],
            "employee_summaries": {},
        }

    try:
        assignments = get_active_published_assignments()
    except Exception as exc:
        print(f"Warning: failed to load active published weekly assignments: {exc}")
        assignments = []

    return {
        "week_start_date": week.get("week_start_date"),
        "assignments": assignments,
        "rows": build_published_weekly_schedule_rows(assignments),
        "employee_summaries": build_employee_schedule_summaries_by_email(assignments),
    }


def build_published_weekly_schedule_rows(assignments):
    rows = []

    for assignment in assignments or []:
        rows.append({
            "day": assignment.get("day_name"),
            "date": assignment.get("work_date"),
            "start": assignment.get("start_time"),
            "end": assignment.get("end_time"),
            "shift_type": assignment.get("shift_type"),
            "employee_name": assignment.get("employee_name") or assignment.get("employee_email"),
            "role": assignment.get("role") or assignment.get("position") or "לא הוגדר תפקיד",
            "notes": assignment.get("notes"),
        })

    return rows


def load_published_weekly_schedule(week_start_date):
    assignments = get_weekly_schedule_assignments(week_start_date, status="published")
    return build_published_weekly_schedule_rows(assignments)


def _parse_work_date(value):
    if isinstance(value, date):
        return value

    return datetime.strptime(value, "%Y-%m-%d").date()


def normalize_schedule_assignments(raw_assignments):
    normalized = []

    for item in raw_assignments or []:
        employee_email = (item.get("employee_email") or "").strip().lower()
        day_name = (item.get("day_name") or "").strip()
        shift_type = (item.get("shift_type") or "").strip()
        work_date_text = (item.get("work_date") or "").strip()

        if not employee_email or not day_name or not shift_type or not work_date_text:
            continue

        if shift_type not in VALID_SHIFT_TYPES:
            continue

        if day_name == "saturday" or (day_name == "friday" and shift_type != "morning"):
            continue

        normalized.append({
            "employee_email": employee_email,
            "employee_name": (item.get("employee_name") or "").strip(),
            "work_date": _parse_work_date(work_date_text),
            "day_name": day_name,
            "shift_type": shift_type,
            "start_time": (item.get("start_time") or "").strip() or None,
            "end_time": (item.get("end_time") or "").strip() or None,
            "notes": (item.get("notes") or "").strip() or None,
        })

    return normalized


def save_weekly_schedule_draft_from_payload(week_start_date, assignments_payload, publish=False):
    try:
        raw_assignments = json.loads(assignments_payload or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid weekly schedule assignments payload.") from exc

    assignments = normalize_schedule_assignments(raw_assignments)
    schedule_id = save_weekly_schedule_draft(week_start_date, assignments, publish=publish)
    open_constraints_week = None
    if publish:
        open_constraints_week = advance_constraints_window_after_publish(week_start_date)

    return {
        "weekly_schedule_id": schedule_id,
        "assignments_count": len(assignments),
        "open_constraints_week": open_constraints_week,
    }


def reset_weekly_schedule_draft(week_start_date):
    return delete_weekly_schedule_draft(week_start_date)


def publish_weekly_schedule_for_employees(week_start_date):
    schedule_id = publish_weekly_schedule(week_start_date)
    open_constraints_week = advance_constraints_window_after_publish(week_start_date)
    return {
        "weekly_schedule_id": schedule_id,
        "open_constraints_week": open_constraints_week,
    }
