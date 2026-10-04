# Pepper Varieties Data Path Class

## Purpose

This document explains the full data path for the pepper varieties page:

```text
GET /pepper-varieties
  -> route
  -> service
  -> repository
  -> SQL tables
  -> template
  -> CSS / JavaScript
```

It also explains how the page shows admin-only buttons such as Add Pepper, Edit, and Delete, while normal visitors cannot see or use those actions.

## Class: PepperVarietiesDataPath

Think about the implementation as this class:

```python
class PepperVarietiesDataPath:
    route_layer = "backend/main.py"
    service_layer = "backend/service/pepper_service.py"
    repository_layer = "backend/data_access/pepper_repository.py"
    heat_repository_layer = "backend/data_access/heat_level_repository.py"
    domain_object = "backend/domain/pepper.py"
    template = "frontend/templates/pepper_varieties.html"
    form_template = "frontend/templates/add_pepper.html"
    css = "frontend/static/css/pepper-varieties.css"
    javascript = "frontend/static/js/pepper-varieties.js"
    schema = "backend/data_access/init_db.py"
```

This is not an app runtime class. It is a documentation class that maps each responsibility to the file where it is implemented.

## 1. Page Load Data Path

When a user opens:

```text
/pepper-varieties
```

Flask calls this route in `backend/main.py`:

```python
def pepper_varieties():
    selected_heat_levels = request.args.getlist("heat_level")
    peppers, selected_heat_levels = list_peppers(selected_heat_levels)
    heat_levels = list_heat_levels()
    return render_template(...)
```

The route reads the selected filter values from the URL query string, asks the service for peppers and heat levels, then renders the Jinja template.

## 2. Filter Data Path

The filter uses heat levels from 0 to 5:

```text
0 = No heat
1 = Mild
2 = Warm
3 = Medium
4 = Hot
5 = Extreme
```

The filter form in `frontend/templates/pepper_varieties.html` sends values like:

```text
/pepper-varieties?heat_level=2&heat_level=4
```

Then:

```text
backend/main.py
  -> list_peppers(["2", "4"])
  -> get_peppers_by_heat_level_values([2, 4])
  -> SQL filters by dbo.pepper_heat_levels.level_value
```

This is important because the UI should use stable business values 0-5, not internal database IDs.

## 3. Heat Level Classification Path

When an admin adds or edits a pepper, the admin enters a numeric Scoville value.

The service runs:

```python
resolve_heat_level(form_data["scoville_level"])
```

That calls `get_heat_level_by_scoville(...)` in `backend/data_access/heat_level_repository.py`.

The database checks which range contains the value:

```sql
WHERE ? BETWEEN min_scoville AND max_scoville
```

Then the pepper is saved with:

```text
scoville_level = the numeric value entered by admin
heat_level_id = the matching row in dbo.pepper_heat_levels
heat_category = the matching heat level name
```

This is how the system automatically classifies every pepper into level 0-5.

## 4. Admin Add Pepper Path

The Add Pepper button is shown only when:

```python
session.get("role") == "admin"
```

The check is inside `frontend/templates/pepper_varieties.html`.

If the user is admin, the template renders:

```text
Add Pepper button -> /admin/peppers/add
```

If the user is a visitor, that HTML is not rendered at all.

The backend also protects the route:

```python
if session.get("role") != "admin":
    return redirect(url_for("pepper_varieties"))
```

So even if a visitor manually types the admin URL, the server blocks the action.

## 5. Admin Edit Pepper Path

Each pepper card renders an Edit button only for admins.

The button opens:

```text
/admin/peppers/<pepper_id>/edit
```

The route:

```text
GET edit route
  -> get_pepper_edit_form(pepper_id)
  -> get_pepper_by_id(pepper_id)
  -> fill add_pepper.html with existing data
```

On submit:

```text
POST edit route
  -> normalize_pepper_form(...)
  -> update_pepper_from_form(...)
  -> validate fields
  -> recalculate heat level from Scoville
  -> update_pepper(...)
  -> clear cache
  -> redirect to /pepper-varieties
```

## 6. Admin Delete Pepper Path

Each pepper card renders a Delete button only for admins.

The button submits a POST request to:

```text
/admin/peppers/<pepper_id>/delete
```

The route checks the admin role again, then calls:

```python
delete_pepper(pepper_id)
```

The service calls:

```python
delete_pepper_by_id(pepper_id)
```

The repository runs:

```sql
DELETE FROM dbo.peppers WHERE id = ?
```

After a successful delete, the pepper cache is cleared and the admin is redirected back to the pepper varieties page.

## 7. Frontend Behavior

`frontend/static/js/pepper-varieties.js` does two client-side jobs:

- Opens the pepper details modal when the image area is clicked.
- Filters visible cards by the search input using each card's `data-search` value.

The heat-level filter is server-side. It reloads `/pepper-varieties` with query parameters so the database returns only the matching peppers.

## 8. Main Files To Explain In Presentation

| Responsibility | File |
| --- | --- |
| Route and admin protection | `backend/main.py` |
| Validation, cache, heat classification | `backend/service/pepper_service.py` |
| Pepper SQL CRUD | `backend/data_access/pepper_repository.py` |
| Heat level SQL lookup | `backend/data_access/heat_level_repository.py` |
| Schema and default 0-5 levels | `backend/data_access/init_db.py` |
| Pepper object | `backend/domain/pepper.py` |
| Pepper page UI | `frontend/templates/pepper_varieties.html` |
| Add/Edit form UI | `frontend/templates/add_pepper.html` |
| Page styling | `frontend/static/css/pepper-varieties.css` |
| Modal and search behavior | `frontend/static/js/pepper-varieties.js` |
