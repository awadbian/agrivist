import time

from backend.data_access.heat_level_repository import (
    get_all_heat_levels,
    get_heat_level_by_scoville,
    get_heat_level_by_value,
)
from backend.data_access.pepper_repository import (
    create_pepper,
    delete_pepper_by_id,
    get_all_peppers,
    get_pepper_by_id,
    get_peppers_by_heat_level_values,
    get_peppers_by_scoville_level,
    update_pepper,
)
from backend.domain.pepper import Pepper


_CACHE_TTL_SECONDS = 60
_pepper_cache = {}
_heat_levels_cache = {"data": None, "expires_at": 0.0}

PEPPER_FORM_FIELDS = (
    "name",
    "scientific_name",
    "origin_country",
    "color",
    "scoville_level",
    "heat_level_value",
    "description",
    "growing_tips",
    "image_url",
    "soil_type",
    "sunlight_needs",
    "temperature_range",
    "watering_needs",
    "irrigation_frequency",
    "water_amount",
    "season",
    "harvest_season",
    "days_to_harvest",
    "harvest_signs",
    "storage_tips",
    "warnings",
)

REQUIRED_TEXT_FIELDS = {
    "name": "Pepper name is required.",
    "scientific_name": "Scientific name is required.",
    "origin_country": "Origin country is required.",
    "color": "Color is required.",
    "description": "Short description is required.",
}


def _is_cache_valid(expires_at):
    return time.time() < expires_at


def clear_pepper_cache():
    _pepper_cache.clear()
    _heat_levels_cache["data"] = None
    _heat_levels_cache["expires_at"] = 0.0


def _normalize_selected_heat_levels(selected_heat_levels):
    if selected_heat_levels is None:
        return []
    if isinstance(selected_heat_levels, (list, tuple)):
        raw_values = selected_heat_levels
    else:
        raw_values = [selected_heat_levels]

    normalized = []
    for value in raw_values:
        value_text = str(value or "").strip()
        if value_text.isdigit():
            normalized.append(value_text)
    return normalized


def list_peppers(selected_heat_levels=None):
    if (
        isinstance(selected_heat_levels, str)
        and selected_heat_levels.strip()
        and not selected_heat_levels.strip().isdigit()
    ):
        legacy_heat_level = selected_heat_levels.strip()
        cached_entry = _pepper_cache.get(legacy_heat_level)
        if cached_entry and _is_cache_valid(cached_entry["expires_at"]):
            return cached_entry["data"], legacy_heat_level

        try:
            peppers = get_peppers_by_scoville_level(legacy_heat_level)
        except Exception as exc:
            print(f"Warning: pepper service failed to load peppers: {exc}")
            peppers = []

        _pepper_cache[legacy_heat_level] = {
            "data": peppers or [],
            "expires_at": time.time() + _CACHE_TTL_SECONDS,
        }
        return peppers or [], legacy_heat_level

    normalized_heat_levels = _normalize_selected_heat_levels(selected_heat_levels)
    cache_key = ",".join(normalized_heat_levels)
    cached_entry = _pepper_cache.get(cache_key)

    if cached_entry and _is_cache_valid(cached_entry["expires_at"]):
        return cached_entry["data"], normalized_heat_levels

    try:
        if normalized_heat_levels:
            peppers = get_peppers_by_heat_level_values([int(value) for value in normalized_heat_levels])
        elif selected_heat_levels and not isinstance(selected_heat_levels, (list, tuple)):
            peppers = get_peppers_by_scoville_level(str(selected_heat_levels).strip())
        else:
            peppers = get_all_peppers()
    except Exception as exc:
        print(f"Warning: pepper service failed to load peppers: {exc}")
        peppers = []

    _pepper_cache[cache_key] = {
        "data": peppers or [],
        "expires_at": time.time() + _CACHE_TTL_SECONDS,
    }

    return peppers or [], normalized_heat_levels


def list_heat_levels():
    if _is_cache_valid(_heat_levels_cache["expires_at"]) and _heat_levels_cache["data"] is not None:
        return _heat_levels_cache["data"]

    try:
        heat_levels = get_all_heat_levels()
    except Exception as exc:
        print(f"Warning: pepper service failed to load heat levels: {exc}")
        heat_levels = []

    _heat_levels_cache["data"] = heat_levels
    _heat_levels_cache["expires_at"] = time.time() + _CACHE_TTL_SECONDS
    return heat_levels


def empty_pepper_form_data():
    return {field_name: "" for field_name in PEPPER_FORM_FIELDS}


def normalize_pepper_form(form):
    form_data = empty_pepper_form_data()
    for field_name in form_data:
        form_data[field_name] = form.get(field_name, "").strip()
    return form_data


def validate_pepper_data(form_data_or_name, scoville_level=None, description=None):
    errors = {}

    if isinstance(form_data_or_name, dict):
        form_data = form_data_or_name
    else:
        form_data = {
            "name": form_data_or_name,
            "scoville_level": scoville_level,
            "description": description,
        }

    for field_name, message in REQUIRED_TEXT_FIELDS.items():
        if not (form_data.get(field_name) or "").strip():
            errors[field_name] = message

    heat_level_value = (form_data.get("heat_level_value") or "").strip()
    scoville_value = (form_data.get("scoville_level") or "").strip()

    if not heat_level_value and not scoville_value:
        errors["heat_level_value"] = "Choose a heat level between 0 and 5."

    if heat_level_value:
        try:
            parsed_heat_level = int(heat_level_value)
            if parsed_heat_level < 0 or parsed_heat_level > 5:
                errors["heat_level_value"] = "Heat level must be between 0 and 5."
        except ValueError:
            errors["heat_level_value"] = "Heat level must be a number between 0 and 5."

    if scoville_value:
        try:
            parsed_scoville = int(scoville_value)
            if parsed_scoville < 0:
                errors["scoville_level"] = "Scoville value must be zero or higher."
        except ValueError:
            errors["scoville_level"] = "Scoville value must be a whole number."

    return errors


def resolve_heat_level_value(level_value):
    try:
        parsed_level_value = int(str(level_value).strip())
    except ValueError:
        return None

    if parsed_level_value < 0 or parsed_level_value > 5:
        return None

    return get_heat_level_by_value(parsed_level_value)


def resolve_heat_level(scoville_level):
    try:
        parsed_scoville = int(str(scoville_level).strip())
    except ValueError:
        return None

    return get_heat_level_by_scoville(parsed_scoville)


def resolve_heat_level_from_form(form_data):
    heat_level_value = (form_data.get("heat_level_value") or "").strip()
    if heat_level_value:
        return resolve_heat_level_value(heat_level_value)

    return resolve_heat_level(form_data.get("scoville_level", ""))


def build_pepper_from_form(form_data, heat_level):
    scoville_text = (form_data.get("scoville_level") or "").strip()
    scoville_level = int(scoville_text) if scoville_text else int(heat_level["level_value"])
    heat_level_name = heat_level["name"] if heat_level else None

    return Pepper(
        name=form_data["name"],
        scientific_name=form_data["scientific_name"],
        origin_country=form_data["origin_country"],
        color=form_data["color"],
        scoville_level=scoville_level,
        heat_level_id=heat_level["id"] if heat_level else None,
        heat_category=heat_level_name,
        heat_level_name=heat_level_name,
        heat_level_color=heat_level["color"] if heat_level else None,
        heat_level_css_class=heat_level["css_class"] if heat_level else None,
        heat_level_description=heat_level["description"] if heat_level else None,
        description=form_data["description"],
        growing_tips=form_data["growing_tips"] or None,
        image_url=form_data["image_url"] or None,
                soil_type=form_data["soil_type"] or None,
        sunlight_needs=form_data["sunlight_needs"] or None,
        temperature_range=form_data["temperature_range"] or None,
        watering_needs=form_data["watering_needs"] or None,
        irrigation_frequency=form_data["irrigation_frequency"] or None,
        water_amount=form_data["water_amount"] or None,
        season=form_data["season"] or None,
        harvest_season=form_data["harvest_season"] or None,
        days_to_harvest=int(form_data["days_to_harvest"]) if form_data["days_to_harvest"] else None,
        harvest_signs=form_data["harvest_signs"] or None,
        storage_tips=form_data["storage_tips"] or None,
        warnings=form_data["warnings"] or None,
    )


def create_pepper_from_form(form_data):
    errors = validate_pepper_data(form_data)
    if errors:
        return None, errors

    heat_level = resolve_heat_level_from_form(form_data)
    if heat_level is None:
        return None, {"heat_level_value": "No matching heat level was found."}

    pepper = build_pepper_from_form(form_data, heat_level)
    pepper_id = create_pepper(pepper)
    if pepper_id is None:
        return None, {"database": "Saving the pepper failed. Please try again later."}

    clear_pepper_cache()
    return pepper_id, {}


def pepper_to_form_data(pepper):
    form_data = empty_pepper_form_data()
    if not pepper:
        return form_data

    for field_name in form_data:
        value = pepper.get(field_name)
        form_data[field_name] = "" if value is None else str(value)

    if not form_data["heat_level_value"] and pepper.get("heat_level_value") is not None:
        form_data["heat_level_value"] = str(pepper.get("heat_level_value"))

    return form_data


def get_pepper_edit_form(pepper_id):
    return pepper_to_form_data(get_pepper_by_id(pepper_id))


def update_pepper_from_form(pepper_id, form_data):
    errors = validate_pepper_data(form_data)
    if errors:
        return False, errors

    heat_level = resolve_heat_level_from_form(form_data)
    if heat_level is None:
        return False, {"heat_level_value": "No matching heat level was found."}

    pepper = build_pepper_from_form(form_data, heat_level)
    pepper.id = pepper_id

    if not update_pepper(pepper):
        return False, {"database": "Pepper update failed. Please try again later."}

    clear_pepper_cache()
    return True, {}


def delete_pepper(pepper_id):
    was_deleted = delete_pepper_by_id(pepper_id)
    if was_deleted:
        clear_pepper_cache()
    return was_deleted
