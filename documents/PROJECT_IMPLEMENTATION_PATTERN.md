# Project Implementation Pattern

## Purpose

Use this document when adding or changing project features. It keeps the implementation ordered and consistent with the current Flask structure.

The project pattern is:

```text
Route
  -> Service
  -> Repository
  -> Domain object when useful
  -> Template / Static assets
  -> Tests
  -> Documentation
```

## 1. Folder Ownership

```text
frontend/templates/        Jinja HTML pages
frontend/static/css/       CSS files
frontend/static/js/        JavaScript files
frontend/static/images/    Images served by Flask

backend/main.py            Flask app setup and route/controller layer
backend/api/               Reserved package for future API routes
backend/domain/            Simple data objects
backend/service/           Business logic, validation, caching
backend/data_access/       SQL Server connection and repository functions
backend/tests/             Pytest tests
backend/tests/unit/        Unit tests
backend/tests/integration/ Integration-style Flask route tests

documents/                 Setup and implementation guide documents
.github/workflows/         GitHub Actions workflows
```

## 2. Request Flow Pattern

Use this mental model for server-rendered pages:

```text
Browser request
  -> backend/main.py route
  -> backend/service function for business rules
  -> backend/data_access repository function for database work
  -> backend/domain object for structured data
  -> frontend/templates Jinja response
  -> frontend/static assets through Flask static route
```

Routes may call repositories directly for very small operations, but new logic should prefer the service layer when validation, rules, or transformations are involved.

## 3. Import Pattern

Always import backend code through the `backend` package:

```python
from backend.service.signup_validation import validate_signup
from backend.service.pepper_service import list_peppers
from backend.data_access.user_repository import get_user_by_email
from backend.domain.user import User
```

Avoid old relative-style imports:

```python
from service.signup_validation import validate_signup
from data_access.user_repository import get_user_by_email
```

Those imports break the separated project structure.

## 4. Route Pattern

Routes live in:

```text
backend/main.py
```

Routes should:

- Read `request.form` or query parameters.
- Call services for validation or business decisions.
- Call repositories only for simple direct data access.
- Set or clear `session` when needed.
- Use `flash(...)` for user-facing success or error messages when useful.
- Render templates from `frontend/templates/`.
- Redirect with `redirect(url_for(...))`.

Example:

```python
@app.route("/example", methods=["GET", "POST"])
def example():
    if request.method == "POST":
        form_data = request.form
        # validate, save, redirect
        return redirect(url_for("home"))

    return render_template("example.html")
```

Current route groups:

| Group | Routes |
| --- | --- |
| Public pages | `/`, `/about`, `/pepper-varieties`, `/tours`, `/book-tour` |
| Auth | `/signup`, `/login`, `/logout`, `/forgot-password` |
| Account | `/profile`, `/delete-account` |
| Tour booking | `/tours/calendar/<id>`, `/tours/time/<id>`, `/tours/details`, `/tours/payment`, `/tours-booking`, `/tour-booking-form` |
| Admin dashboard | `/admin-dashboard` |
| Admin users/bookings | `/admin/users/<id>/deactivate`, `/admin/users/<id>/activate`, `/admin/bookings/<id>/cancel` |
| Admin peppers | `/admin/add-pepper`, `/admin/peppers/add`, `/admin/peppers/<id>/edit`, `/admin/peppers/<id>/delete` |
| Admin tours | `/admin/add-tour`, `/admin/tours/add`, `/admin/tours/<id>/edit`, `/admin/tours/<id>/delete` |

## 5. Service Pattern

Services live in:

```text
backend/service/
```

Use services for:

- Validation.
- Form normalization.
- Business decisions.
- Cache handling.
- Combining multiple repository calls.
- Creating domain objects from request data.

Current services:

| File | Responsibility |
| --- | --- |
| `signup_validation.py` | Signup field validation |
| `pepper_service.py` | Pepper list/filter/cache/form logic |
| `tour_service.py` | Tour package form normalization, validation, and CRUD logic |
| `admin_service.py` | Optional admin user setup |

Services may call repositories. Services should not render templates or read Flask request objects directly unless the existing pattern already requires it.

## 6. Repository Pattern

Repositories live in:

```text
backend/data_access/
```

Use repositories for SQL and database access.

Rules:

- Use `pyodbc` placeholders with `?`.
- Do not concatenate user input into SQL.
- Close cursors and connections.
- Return predictable values such as dictionaries, lists, `None`, IDs, or booleans.
- Keep SQL Server schema details out of route code when possible.

Example:

```python
cursor.execute("SELECT * FROM dbo.users WHERE email = ?", (email,))
```

Current repositories:

| File | Responsibility |
| --- | --- |
| `db.py` | Connection loading and helpers |
| `init_db.py` | Schema creation and migration helpers |
| `role_repository.py` | Role lookup |
| `user_repository.py` | User CRUD |
| `pepper_repository.py` | Pepper create/read/filter/count |
| `heat_level_repository.py` | Pepper heat-level lookup |
| `tour_booking_repository.py` | Booking create/list/cancel helpers |
| `tour_repository.py` | Tour package CRUD helpers |
| `tour_package_repository.py` | Compatibility wrapper around tour repository helpers |

## 7. Domain Pattern

Domain objects live in:

```text
backend/domain/
```

Current objects:

```text
user.py       User
pepper.py     Pepper
tour.py       Tour
```

Domain objects should be simple containers. They should not import Flask, render templates, open database connections, or contain SQL.

## 8. Template Pattern

Templates live in:

```text
frontend/templates/
```

Templates should:

- Use Jinja variables passed from route functions.
- Use `{% include 'line.html' %}` for shared navigation where needed.
- Use `url_for(...)` for app routes and static files.
- Preserve Hebrew / RTL layout conventions.
- Avoid SQL, database logic, or complex business rules.

Static file example:

```jinja
{{ url_for('static', filename='images/pepper-hero.jpg') }}
```

## 9. Static Asset Pattern

Static files live in:

```text
frontend/static/
```

Use:

```text
css/
js/
images/
```

Flask serves static files through the normal `static` endpoint because `backend/main.py` sets `static_folder` to `frontend/static`.

## 10. Database Pattern

Database setup lives in:

```text
backend/data_access/init_db.py
```

Connection setup lives in:

```text
backend/data_access/db.py
```

Current tables:

```text
dbo.roles
dbo.users
dbo.peppers
dbo.pepper_heat_levels
dbo.tour_bookings
dbo.tour_packages
```

Application roles:

```text
visitor
admin
employee
```

Schema conventions:

- SQL Server syntax.
- `dbo` schema.
- `IDENTITY(1,1)` IDs.
- `NVARCHAR` for text.
- `?` placeholders for query values.

## 11. Authentication Pattern

Login stores:

```python
session["user_id"] = user["id"]
session["user"] = user["full_name"]
session["email"] = user["email"]
session["role"] = user["role"]
```

Logout clears:

```python
session.clear()
```

Admin checks use:

```python
session.get("role") == "admin"
```

Passwords must use:

```python
generate_password_hash(...)
check_password_hash(...)
```

## 12. Testing Pattern

Tests live in:

```text
backend/tests/
backend/tests/unit/
backend/tests/integration/
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
```

Testing rules:

- Route tests should use Flask's test client.
- Monkeypatch imported route dependencies where they are used.
- Service tests should avoid real database calls.
- Repository tests can fake the connection and cursor.
- Normal CI tests should not require real Azure SQL.

## 13. CI/CD Pattern

GitHub Actions workflows live in:

```text
.github/workflows/
```

The workflow should:

- Install Python dependencies.
- Compile backend files.
- Run lint checks.
- Import `backend.main` as a smoke check.
- Run pytest.
- Upload the pytest report.
- Deploy the packaged Flask app only after quality checks pass.

## 14. Adding A Feature Checklist

1. Decide which layers the feature needs.
2. Add or update a domain object if structured data is useful.
3. Add or update schema in `backend/data_access/init_db.py` if needed.
4. Add repository functions in `backend/data_access/`.
5. Add validation or business rules in `backend/service/`.
6. Add or update routes in `backend/main.py`.
7. Add templates in `frontend/templates/`.
8. Add CSS, JS, or images under `frontend/static/`.
9. Add focused tests under `backend/tests/`.
10. Update docs when behavior, setup, routes, schema, or folder structure changes.

## 15. Things To Avoid

- Do not recreate a `src/` folder.
- Do not move templates or static assets into `backend/`.
- Do not use old imports such as `from service...`.
- Do not put SQL inside templates.
- Do not put database code inside domain classes.
- Do not store plain-text passwords.
- Do not hardcode local absolute paths.
- Do not commit `.env`, `documents/.env`, `appsettings.json`, or real credentials.
