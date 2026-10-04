from datetime import date, timedelta

from backend.data_access.employee_schedule_settings_repository import get_closed_days_for_week
from backend.data_access.worker_constraints_repository import (
    get_worker_constraints,
    save_worker_constraints,
)
from backend.data_access.weekly_schedule_repository import (
    CONSTRAINTS_STATUS_OPEN,
    get_open_constraints_week,
    get_weekly_schedule_week,
)

WORK_DAYS = (
    ("sunday", "ראשון"),
    ("monday", "שני"),
    ("tuesday", "שלישי"),
    ("wednesday", "רביעי"),
    ("thursday", "חמישי"),
    ("friday", "שישי"),
)

AVAILABILITY_OPTIONS = (
    ("morning", "בוקר"),
    ("evening", "ערב"),
    ("all_day", "זמין/ה כל היום"),
    ("unavailable", "יום חופש / לא זמין/ה"),
)

LEGACY_AVAILABILITY_LABELS = {
    "midday": "אמצע יום",
}
VALID_AVAILABILITY_VALUES = {value for value, _label in AVAILABILITY_OPTIONS} | set(LEGACY_AVAILABILITY_LABELS)
MIN_AVAILABLE_DAYS = 4
MIN_AVAILABLE_DAYS_ERROR = "עליך לבחור לפחות 4 משמרות זמינות לשבוע הבא."
MIN_AVAILABLE_DAYS_ERROR_EN = "You must choose at least 4 available shifts for next week."
NO_ACTIVE_CONSTRAINT_WEEK_MESSAGE = "אין כרגע שבוע פעיל להגשת אילוצים."
INVALID_AVAILABILITY_ERROR = "יש לבחור אפשרות אחת עבור כל יום לפני שליחת האילוצים."
CONSTRAINT_UPDATES_CLOSED_MESSAGE = "המנהל סגר את אפשרות עדכון האילוצים לשבוע זה."
CONSTRAINT_SUBMISSION_CLOSED_MESSAGE = "אפשרות הגשת האילוצים לשבוע זה נסגרה על ידי המנהל."
PUBLISHED_WEEK_CONSTRAINTS_CLOSED_MESSAGE = "Constraints are closed for a week that already has a published schedule."
CLOSED_DAY_MESSAGE = "This day is closed and constraints cannot be submitted for it."


FRIDAY_AVAILABILITY_OPTIONS = (
    ("morning", "בוקר"),
    ("unavailable", "יום חופש / לא זמין/ה"),
)


def get_availability_options_for_day(day_value):
    if day_value == "friday":
        return FRIDAY_AVAILABILITY_OPTIONS

    return AVAILABILITY_OPTIONS


def get_availability_options_by_day():
    return {
        day_value: get_availability_options_for_day(day_value)
        for day_value, _day_label in WORK_DAYS
    }


def get_next_week_start(today=None):
    current_date = today or date.today()
    current_week_sunday = current_date - timedelta(days=(current_date.weekday() + 1) % 7)
    return current_week_sunday + timedelta(days=7)


def are_constraint_updates_open(week_start_date):
    if week_start_date is None:
        return False

    try:
        week = get_weekly_schedule_week(week_start_date)
    except Exception as exc:
        print(f"Warning: failed to load constraints update status: {exc}")
        return False

    return bool(week and week.get("constraints_status") == CONSTRAINTS_STATUS_OPEN)


def is_published_schedule_week(week_start_date):
    if week_start_date is None:
        return False

    try:
        week = get_weekly_schedule_week(week_start_date)
    except Exception as exc:
        print(f"Warning: failed to load weekly schedule lock: {exc}")
        return False

    return bool(week and week.get("status") == "published")


def get_active_constraints_week_start():
    try:
        active_week = get_open_constraints_week()
    except Exception as exc:
        print(f"Warning: failed to load active constraints week: {exc}")
        return None

    return active_week.get("week_start_date") if active_week else None


def normalize_constraints_submission(form, closed_days=None):
    availability = {}
    available_days_count = 0
    closed_days = set(closed_days or ())

    for day_value, _day_label in WORK_DAYS:
        if day_value in closed_days:
            availability[day_value] = "unavailable"
            continue

        selected_value = (form.get(f"availability_{day_value}") or "").strip()
        valid_day_values = {
            value for value, _label in get_availability_options_for_day(day_value)
        }
        if day_value != "friday":
            valid_day_values |= set(LEGACY_AVAILABILITY_LABELS)

        if selected_value not in valid_day_values:
            return None, INVALID_AVAILABILITY_ERROR

        availability[day_value] = selected_value
        if selected_value != "unavailable":
            available_days_count += 1

    if available_days_count < MIN_AVAILABLE_DAYS:
        return None, MIN_AVAILABLE_DAYS_ERROR

    notes = (form.get("constraints_notes") or "").strip()
    return {"availability": availability, "notes": notes}, None


def get_closed_constraint_days(week_start_date):
    closed_days = {"saturday"}

    try:
        for row in get_closed_days_for_week(week_start_date):
            if row.get("is_closed"):
                closed_days.add(row.get("day_name"))
    except Exception as exc:
        print(f"Warning: failed to load closed constraint days: {exc}")

    return closed_days


def get_existing_constraints(employee_email, today=None):
    week_start_date = get_active_constraints_week_start()
    if week_start_date is None:
        return None, None

    submission = get_worker_constraints(employee_email, week_start_date)
    return submission, week_start_date


def submit_worker_constraints(employee_email, form, today=None):
    existing_submission, week_start_date = get_existing_constraints(employee_email, today)

    if week_start_date is None:
        return None, None, NO_ACTIVE_CONSTRAINT_WEEK_MESSAGE, False

    if is_published_schedule_week(week_start_date):
        return (
            existing_submission,
            week_start_date,
            PUBLISHED_WEEK_CONSTRAINTS_CLOSED_MESSAGE,
            False,
        )

    if not are_constraint_updates_open(week_start_date):
        return (
            existing_submission,
            week_start_date,
            CONSTRAINT_UPDATES_CLOSED_MESSAGE if existing_submission else CONSTRAINT_SUBMISSION_CLOSED_MESSAGE,
            False,
        )

    closed_days = get_closed_constraint_days(week_start_date)
    submission_data, error = normalize_constraints_submission(form, closed_days)
    if error:
        return None, week_start_date, error, False

    save_worker_constraints(
        employee_email,
        week_start_date,
        submission_data["availability"],
        submission_data["notes"],
    )

    saved_submission = get_worker_constraints(employee_email, week_start_date)
    return saved_submission, week_start_date, None, True
