from datetime import datetime

from backend.data_access.tour_repository import (
    create_tour,
    delete_tour_by_id,
    get_active_tour_by_id,
    get_active_tours,
    get_all_tours,
    get_tour_by_id,
    update_tour,
)
from backend.domain.tour import Tour

TOUR_FORM_FIELDS = (
    "title",
    "price",
    "duration_minutes",
    "max_people",
    "description",
    "includes",
    "image_url",
    "available_from",
    "available_until",
    "is_active",
)


def empty_tour_form_data():
    return {field_name: "" for field_name in TOUR_FORM_FIELDS}


def normalize_tour_form(form):
    form_data = empty_tour_form_data()
    for field_name in TOUR_FORM_FIELDS:
        if field_name == "is_active":
            form_data[field_name] = form.get(field_name) is not None
        else:
            form_data[field_name] = form.get(field_name, "").strip()
    return form_data


def _parse_positive_int(value, field_name, errors, message):
    try:
        parsed = int(str(value or "").strip())
    except ValueError:
        errors[field_name] = message
        return None

    if parsed <= 0:
        errors[field_name] = message
        return None

    return parsed


def _validate_date_range(form_data, errors):
    start = form_data.get("available_from")
    end = form_data.get("available_until")
    if not start or not end:
        return

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        errors["available_from"] = "יש להזין תאריכים תקינים."
        return

    if start_date > end_date:
        errors["available_until"] = "תאריך הסיום חייב להיות אחרי תאריך ההתחלה."


def validate_tour_data(form_data):
    errors = {}

    if not form_data.get("title"):
        errors["title"] = "יש להזין שם סיור."

    if not form_data.get("description"):
        errors["description"] = "יש להזין תיאור לסיור."

    if not form_data.get("includes"):
        errors["includes"] = "יש להזין מה כלול בסיור."

    if not form_data.get("image_url"):
        errors["image_url"] = "יש לבחור תמונה לסיור."

    if not form_data.get("available_from"):
        errors["available_from"] = "יש לבחור תאריך התחלה."

    if not form_data.get("available_until"):
        errors["available_until"] = "יש לבחור תאריך סיום."

    _parse_positive_int(
        form_data.get("price"),
        "price",
        errors,
        "יש להזין מחיר תקין.",
    )

    _parse_positive_int(
        form_data.get("duration_minutes"),
        "duration_minutes",
        errors,
        "יש להזין משך סיור תקין בדקות.",
    )

    _parse_positive_int(
        form_data.get("max_people"),
        "max_people",
        errors,
        "יש להזין מספר משתתפים מקסימלי תקין.",
    )

    _validate_date_range(form_data, errors)

    return errors


def build_tour_from_form(form_data, tour_id=None):
    return Tour(
        tour_id=tour_id,
        title=form_data["title"],
        price=int(form_data["price"]),
        duration_minutes=int(form_data["duration_minutes"]),
        max_people=int(form_data["max_people"]),
        description=form_data["description"],
        includes=form_data["includes"],
        image_url=form_data.get("image_url") or None,
        available_from=form_data.get("available_from") or None,
        available_until=form_data.get("available_until") or None,
        is_active=bool(form_data.get("is_active")),
    )


def tour_to_form_data(tour):
    form_data = empty_tour_form_data()
    if not tour:
        form_data["is_active"] = True
        return form_data

    for field_name in form_data:
        value = tour.get(field_name)
        form_data[field_name] = "" if value is None else str(value)

    form_data["is_active"] = bool(tour.get("is_active", True))
    return form_data


def create_tour_from_form(form_data):
    errors = validate_tour_data(form_data)
    if errors:
        return None, errors

    tour_id = create_tour(build_tour_from_form(form_data))
    if tour_id is None:
        return None, {"database": "שמירת הסיור נכשלה. נסו שוב מאוחר יותר."}

    return tour_id, {}


def update_tour_from_form(tour_id, form_data):
    errors = validate_tour_data(form_data)
    if errors:
        return False, errors

    if not update_tour(build_tour_from_form(form_data, tour_id=tour_id)):
        return False, {"database": "עדכון הסיור נכשל. נסו שוב מאוחר יותר."}

    return True, {}


def delete_tour(tour_id):
    return delete_tour_by_id(tour_id)


def get_tour_edit_form(tour_id):
    return tour_to_form_data(get_tour_by_id(tour_id))


def list_active_tours():
    return get_active_tours()


def list_admin_tours():
    return get_all_tours()


def get_active_tour(tour_id):
    return get_active_tour_by_id(tour_id)
