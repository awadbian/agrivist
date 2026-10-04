# Implementation Guide

## Goal Of This Document

This guide explains how the project is implemented so a developer or GPT assistant can safely continue the work. The project uses a separated frontend and backend, while the backend keeps a simple layered Flask architecture.

## Project Shape

```text
BS-PMC-26-TEAM4/
  frontend/
    templates/
      admin/
    static/
      css/
      js/
      images/
        tours/

  backend/
    __init__.py
    main.py
    api/
    domain/
    service/
    data_access/
    tests/

  documents/
  requirements.txt
  README.md
  .env
  .gitignore
```

`frontend/` contains the user interface files. `backend/` contains the Python application, business rules, data access code, domain objects, and tests.

## Runtime Entry Point

The app entry point is:

```text
backend/main.py
```

Run from the project root:

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

Because that command executes a file inside `backend/`, `backend/main.py` adds the project root to `sys.path` before importing backend packages. This keeps imports like this working:

```python
from backend.service.signup_validation import validate_signup
from backend.data_access.user_repository import get_user_by_email
from backend.domain.user import User
```

## Flask Template And Static Setup

Templates and static assets are not inside `backend/`. Flask is configured in `backend/main.py` to load them from `frontend/`:

```python
ROOT_DIR = Path(__file__).resolve().parents[1]

app = Flask(
    __name__,
    template_folder=str(ROOT_DIR / "frontend" / "templates"),
    static_folder=str(ROOT_DIR / "frontend" / "static"),
)
```

This means:

- `render_template("index.html")` loads `frontend/templates/index.html`.
- `render_template("admin/admin_dashboard.html")` loads `frontend/templates/admin/admin_dashboard.html`.
- `url_for("static", filename="images/about-hero.jpg")` serves `frontend/static/images/about-hero.jpg`.
- Uploaded tour images are saved under `frontend/static/images/tours/`.

Do not move templates or static files back under `backend/`.

## Backend Layers

The backend follows this flow:

```text
Route function
  -> Service function
  -> Repository function
  -> Database
```

Routes may also directly call repositories for simple operations, which is part of the current implementation.

### Route Layer

File:

```text
backend/main.py
```

Responsibilities:

- Define Flask routes.
- Read `request.form`, `request.files`, and query parameters.
- Set and clear `session`.
- Call services and repositories.
- Render Jinja templates.
- Redirect with `url_for(...)`.
- Use `flash(...)` for user-facing status messages.

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

### Service Layer

Folder:

```text
backend/service/
```

Files:

```text
signup_validation.py      Validates signup fields
pepper_service.py         Pepper list/filter/cache/form logic
tour_service.py           Tour package form, validation, CRUD logic
admin_service.py          Optional admin user creation/update
```

Use the service layer for business rules, validation, transformations, and cache decisions.

### Data Access Layer

Folder:

```text
backend/data_access/
```

Files:

```text
db.py                         Loads config and opens pyodbc connections
init_db.py                    Creates and migrates SQL Server tables
role_repository.py            Role lookup helpers
user_repository.py            User queries and updates
pepper_repository.py          Pepper queries and CRUD helpers
heat_level_repository.py      Pepper heat-level lookup helpers
tour_booking_repository.py    Tour booking queries and updates
tour_repository.py            Tour package CRUD helpers
tour_package_repository.py    Compatibility wrapper around tour_repository
```

Repository functions should contain SQL. Use `?` placeholders with `pyodbc`:

```python
cursor.execute("SELECT * FROM dbo.users WHERE email = ?", (email,))
```

Do not build SQL by concatenating form input or query parameters.

### Domain Layer

Folder:

```text
backend/domain/
```

Files:

```text
user.py       User data object
pepper.py     Pepper data object
tour.py       Tour data object
```

Domain classes should stay lightweight. They should not open database connections, read Flask requests, or render templates.

## Database Configuration

`backend/data_access/db.py` loads `.env` from the project root.

Connection settings are checked in this order:

1. `AZURE_SQL_CONNECTION_STRING`
2. `ConnectionStrings__MyDbConnection`
3. `ConnectionStrings_MyDbConnection`
4. `appsettings.json` with `ConnectionStrings.MyDbConnection`
5. Separate `AZURE_SQL_SERVER`, `AZURE_SQL_DATABASE`, `AZURE_SQL_USERNAME`, and `AZURE_SQL_PASSWORD`

The code can normalize ASP.NET-style SQL Server connection strings for ODBC. If a full connection string does not include `DRIVER=...`, the app chooses an installed SQL Server ODBC driver.

## Database Tables

Tables are created and updated in:

```text
backend/data_access/init_db.py
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

`dbo.roles` stores:

```text
visitor
admin
employee
```

`dbo.users` stores users and points to `dbo.roles` through `role_id`. New signup users receive the `visitor` role.

`dbo.peppers` stores pepper varieties and display fields.

`dbo.pepper_heat_levels` stores stable heat levels. The UI uses `level_value` values from 0 to 5, while `id` stays an internal database key.

`dbo.tour_bookings` stores submitted tour booking requests and booking status.

`dbo.tour_packages` stores tour packages, prices, descriptions, image URLs, availability dates, and active/inactive status.

## Authentication And Authorization

Authentication is session-based.

On successful login:

```python
session["user_id"] = user["id"]
session["user"] = user["full_name"]
session["email"] = user["email"]
session["role"] = user["role"]
```

On logout:

```python
session.clear()
```

Admin-only pages check:

```python
session.get("role") == "admin"
```

Passwords are handled with Werkzeug:

```python
generate_password_hash(password)
check_password_hash(user["password_hash"], password)
```

## Feature Flows

### Signup

```text
POST /signup
  -> read form fields
  -> validate_signup(...)
  -> get_user_by_email(...)
  -> generate_password_hash(...)
  -> create User(...)
  -> create_user(...)
  -> set session
  -> redirect home
```

### Pepper List

```text
GET /pepper-varieties
  -> read optional heat_level query parameters
  -> list_peppers(selected_heat_levels)
  -> list_heat_levels()
  -> render pepper_varieties.html
```

### Admin Pepper Management

```text
GET/POST /admin/peppers/add
  -> require admin
  -> normalize_pepper_form(...)
  -> create_pepper_from_form(...)
  -> clear cache
  -> redirect pepper list

GET/POST /admin/peppers/<id>/edit
  -> require admin
  -> get_pepper_edit_form(...)
  -> normalize_pepper_form(...)
  -> update_pepper_from_form(...)
  -> recalculate heat level
  -> clear cache
  -> redirect pepper list

POST /admin/peppers/<id>/delete
  -> require admin
  -> delete_pepper(...)
  -> clear cache
  -> redirect pepper list
```

### Tour Browsing And Booking

```text
GET /tours
  -> list_active_tours()
  -> fallback to default tour packages if database is unavailable or empty
  -> render tours.html

GET/POST /tours/calendar/<tour_package_id>
  -> load active tour
  -> validate selected date
  -> store draft in session
  -> redirect to time step

GET/POST /tours/time/<tour_package_id>
  -> validate draft and available slot
  -> validate participants
  -> calculate total price
  -> redirect to details step

GET/POST /tours/details
  -> require complete draft
  -> require logged-in user on submit
  -> validate visitor details and email
  -> redirect to payment step

GET/POST /tours/payment
  -> require complete draft
  -> save booking through create_tour_booking(...)
  -> clear draft
```

### Admin Tour Management

```text
GET/POST /admin/tours/add
  -> require admin
  -> normalize_tour_form(...)
  -> save uploaded image if provided
  -> create_tour_from_form(...)
  -> redirect tours page

GET/POST /admin/tours/<id>/edit
  -> require admin
  -> get_tour_edit_form(...)
  -> save replacement image if provided
  -> update_tour_from_form(...)
  -> redirect tours page

POST /admin/tours/<id>/delete
  -> require admin
  -> block delete if active paid bookings exist
  -> delete_tour(...)
  -> redirect tours page
```

### Admin Dashboard

```text
GET /admin-dashboard
  -> require admin
  -> load users, workers, bookings, peppers, tours
  -> calculate dashboard stats
  -> render admin/admin_dashboard.html

POST /admin/users/<id>/deactivate
POST /admin/users/<id>/activate
POST /admin/bookings/<id>/cancel
  -> require admin
  -> update target record
  -> redirect dashboard
```

## Testing

Tests live in:

```text
backend/tests/
  unit/
  integration/
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
```

Test conventions:

- Route tests use Flask's test client.
- Tests monkeypatch functions where they are imported.
- Repository tests use fake cursors/connections where possible.
- Normal test runs should not require real Azure SQL credentials.
- `backend/tests/db_test.py` is a manual database connection helper, not a normal unit test.

## Quality Pipeline

GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

Current commands:

```text
python -m compileall backend
flake8 backend --select=E9,F63,F7,F82 --max-line-length=120
python -c "from backend.main import app; print(app.name)"
pytest backend/tests --junitxml=test-results/pytest-report.xml
```

The workflow deploys to Azure Web App only after the quality check job succeeds.

## Adding A New Feature

Use this sequence:

1. Add or update a data object in `backend/domain/` if needed.
2. Add or update schema in `backend/data_access/init_db.py` if needed.
3. Add repository functions in `backend/data_access/`.
4. Add validation or business rules in `backend/service/`.
5. Add or update route functions in `backend/main.py`.
6. Add or update templates in `frontend/templates/`.
7. Add CSS, JS, or images under `frontend/static/`.
8. Add focused tests under `backend/tests/`.
9. Update README and documents if paths, setup, schema, routes, or conventions changed.

## Non-Negotiable Conventions

- Use `backend.*` imports.
- Keep frontend files under `frontend/`.
- Keep SQL in `backend/data_access/`.
- Keep business rules in `backend/service/`.
- Keep route code in `backend/main.py` unless a larger blueprint refactor is explicitly requested.
- Use `url_for(...)` for internal links and static assets.
- Use SQL parameters, not string-built SQL with user input.
- Hash passwords.
- Do not commit secrets.
