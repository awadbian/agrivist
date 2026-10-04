# AgriVisit - Digital Platform for an Agricultural Visitor Center

AgriVisit היא אפליקציית Web לניהול מרכז מבקרים חקלאי בחוות פלפלים. המערכת מחברת בין מבקרים, עובדים ומנהלים במקום אחד: מבקרים יכולים להכיר את החווה ולהזמין סיורים, עובדים יכולים לראות סידור עבודה ולהגיש אילוצים, ומנהלים יכולים לנהל את התוכן, ההזמנות והעבודה התפעולית.

ה-README הזה מתאר את המימוש הנוכחי האמיתי של הפרויקט לפני ההגנה.

## 1. Project Overview

AgriVisit נבנתה עבור חוות פלפלים / מרכז מבקרים חקלאי שצריך לנהל גם אתר מידע וגם תפעול פנימי.

המערכת פותרת כמה צרכים מרכזיים:

* הצגת מידע על החווה, זני פלפלים וסיורים.
* הרשמה והתחברות של משתמשים.
* הזמנת סיורים ותיעוד תשלום פנימי.
* ניהול פלפלים, סיורים, הזמנות ומשתמשים על ידי מנהל.
* ניהול עובדים, אילוצים וסידור עבודה שבועי.
* התראות, משובים, דירוגים ומועמדויות עבודה.

משתמשים מרכזיים:

* Public visitor: מבקר לא מחובר שצופה בתוכן ציבורי.
* Logged-in visitor: מבקר מחובר שיכול להזמין סיורים, לראות הזמנות, לשלוח משוב ולהגיש מועמדות.
* Employee / worker: עובד שרואה סידור עבודה, מגיש אילוצים ורואה משימות/סיורים.
* Admin: מנהל שמנהל את המערכת ואת סידור העבודה.

הערך המרכזי של המערכת הוא חיבור בין חוויית מבקר לבין ניהול פנימי של חווה חקלאית.

## 2. Implemented Features

### Sprint 1

מימוש בסיס המערכת:

* Home page - דף הבית הציבורי של החווה.
* About page - מידע על החווה.
* Signup - הרשמת visitor חדש.
* Login / Logout - התחברות והתנתקות עם session.
* Forgot password - איפוס סיסמה לפי אימייל ושם.
* Profile - צפייה ועדכון פרופיל למשתמש מחובר.
* Basic pepper varieties page - צפייה בזני פלפלים וסינון בסיסי.

קבצים מרכזיים:

* `backend/main.py`
* `backend/service/signup_validation.py`
* `backend/data_access/user_repository.py`
* `frontend/templates/index.html`
* `frontend/templates/signup.html`
* `frontend/templates/login.html`
* `frontend/templates/profile.html`
* `frontend/templates/pepper_varieties.html`

### Sprint 2

מימוש חוויית מבקר וניהול תוכן:

* Pepper varieties management.
* חיפוש וסינון פלפלים לפי רמות חריפות.
* Admin add/edit/delete pepper.
* Tour packages.
* Multi-step tour booking:
  * בחירת סיור.
  * בחירת תאריך.
  * בחירת שעה ומספר משתתפים.
  * הכנסת פרטים.
  * אישור תשלום.
* Payment records - תיעוד תשלום פנימי בטבלת `payments`.
* My booked tours - צפייה בהזמנות ששולמו.
* Booking cancellation - ביטול הזמנה אם נשארו לפחות יומיים.
* Website feedback.
* Tour reviews.
* Admin dashboard.

חלקים חשובים:

* התשלום אינו חיבור לספק סליקה חיצוני, אלא רשומת תשלום פנימית.
* קיימים גם מסלולי הזמנה ישנים/מקבילים כמו `/tours-booking` ו-`/tour-booking-form`; המסלול המרכזי הוא דרך `/tours`.

### Sprint 3

מימוש הצד התפעולי של עובדים ומנהלים:

* Worker dashboard.
* Worker constraints submission.
* Admin weekly work schedule.
* Weekly schedule save / publish / reset.
* Open / close constraints window.
* Closed days.
* Worker personal schedule.
* Worker assigned tours - ממומש חלקית, השיוך בסיסי לפי עובד זמין.
* Shift status / attendance.
* Job applications.
* Admin approve/reject applications.
* Notifications לעובדים ולמנהלים.

חלקים חשובים:

* עובדים רואים רק סידור עבודה שפורסם (`published`).
* מנהל משבץ עובדים ידנית; אין עדיין אלגוריתם אוטומטי שמייצר סידור מאילוצים.
* אילוצי עובדים נשמרים בטבלאות SQL מנורמלות, לא ב-JSON.
* ימים סגורים משפיעים גם על טופס האילוצים וגם על לוח השיבוץ.

## 3. User Roles and Permissions

### Public visitor

יכול לראות:

* `/`
* `/about`
* `/pepper-varieties`
* `/tours`
* `/signup`
* `/login`
* `/forgot-password`

לא יכול:

* לבצע הזמנה בפועל בלי login.
* לגשת לדפי עובד.
* לגשת לדפי מנהל.

### Logged-in visitor

יכול:

* לעדכן פרופיל דרך `/profile`.
* להזמין סיור.
* לראות הזמנות ב-`/my-booked-tours`.
* לבטל הזמנה לפי כלל יומיים.
* לשלוח משוב אתר.
* לדרג סיור אם קיימת הזמנה מתאימה.
* להגיש מועמדות לעבודה דרך `/job-application`.

לא יכול:

* לנהל פלפלים, סיורים, עובדים או סידור עבודה.
* להיכנס לדפי עובד או מנהל.

### Employee / worker

יכול:

* לראות סידור עבודה אישי ב-`/employee-schedule`.
* לראות דשבורד עובד ב-`/worker-dashboard`.
* להגיש אילוצים ב-`/worker-constraints`.
* לראות סיורים שהוקצו לו ב-`/worker-tours`.
* לראות סטטוס משמרת ולוח משמרות.
* להתחיל ולסיים משמרת.
* לראות התראות.
* לראות מפת חווה.

לא יכול:

* לגשת לדשבורד מנהל.
* לנהל סיורים או פלפלים.
* לפתוח/לסגור חלון אילוצים.
* לשמור או לפרסם סידור עבודה.

### Admin

יכול:

* לראות דשבורד מנהל.
* לנהל משתמשים.
* לנהל פלפלים.
* לנהל סיורים.
* לראות הזמנות ותשלומים.
* לבטל הזמנות.
* לאשר/לדחות מועמדויות עבודה.
* לנהל סידור עבודה שבועי.
* לפתוח/לסגור חלון אילוצים.
* לסמן ימים סגורים.
* לראות התראות.

לא יכול:

* להגיש אילוצים כעובד דרך דף employee-only.

הרשאות מיושמות בעיקר ב-`backend/main.py` בעזרת `session.get("role")`.

## 4. System Architecture

הפרויקט בנוי בארכיטקטורה שכבתית פשוטה:

```text
UI / HTML form
-> Flask route in backend/main.py
-> service layer
-> data_access / repository layer
-> SQL Server / Azure SQL
-> Jinja2 template response
```

תיקיות וקבצים חשובים:

```text
backend/
  main.py                 Flask app, routes, session checks
  service/                Business logic and validation
  data_access/            SQL repositories and DB connection
  domain/                 Simple data objects
  tests/                  pytest tests

frontend/
  templates/              Jinja2 templates
  static/css/             CSS files
  static/js/              JavaScript files
  static/images/          Images and uploaded tour images

documents/                Project documentation for defense
.github/workflows/CI.yml  CI/CD workflow
requirements.txt          Python dependencies
```

טכנולוגיות:

* Python
* Flask 2.3.3
* Jinja2 templates
* SQL Server / Azure SQL
* pyodbc
* python-dotenv
* Werkzeug password hashing
* pytest
* GitHub Actions

משתני סביבה נטענים דרך `.env`, `appsettings.json` או Application Settings בענן.

## 5. Database Summary

המערכת משתמשת ב-SQL Server / Azure SQL.

אזורי DB מרכזיים:

* Users and roles: `users`, `roles`
* Peppers: `peppers`, `pepper_heat_levels`
* Tours and bookings: `tour_packages`, `tour_bookings`
* Payments: `payments`
* Feedback and reviews: `website_feedback`, `tour_ratings`
* Notifications: `notifications`
* Job applications: `job_applications`
* Worker constraints: `employee_constraint_submissions`, `employee_constraint_days`
* Weekly schedule: `weekly_schedule_weeks`, `weekly_schedule_assignments`, `employee_schedule_closed_days`
* Employee schedule / attendance: `employee_profiles`, `employee_shifts`, `employee_attendance`

קיימות גם טבלאות legacy של אילוצים שהקוד יודע לקרוא לצורך מיגרציה אם הן קיימות:

* `employee_constraints`
* `worker_constraint_submissions`
* `worker_constraint_days`

לתיעוד מלא של בסיס הנתונים ראו:

* [documents/DATABASE.md](documents/DATABASE.md)

## 6. UI Pages Summary

אזורי UI מרכזיים:

### Public pages

* Home page
* About
* Pepper varieties
* Tours
* Signup
* Login
* Forgot password

### Visitor pages

* Profile
* Multi-step tour booking
* Payment confirmation
* My booked tours
* Website feedback
* Post-tour review
* Job application

### Employee pages

* Worker dashboard
* Worker constraints
* Employee schedule
* Worker tours
* Shift status
* Weekly shift calendar
* Farm map
* Notifications

### Admin pages

* Admin dashboard
* Add/edit/delete pepper
* Add/edit/delete tour
* Weekly schedule
* Work planning legacy pages
* Job application approve/reject
* Notifications

לתיעוד מלא של מסכי UI, routes, הרשאות ופעולות ראו:

* [documents/UI.md](documents/UI.md)

## 7. Testing and Quality

בדיקות נמצאות ב:

```text
backend/tests
```

המערכת משתמשת ב-`pytest`.

סוגי בדיקות קיימים:

* Unit tests.
* Flask route / integration tests.
* Repository tests עם fake connection/cursor.
* Validation tests.
* Smoke tests.
* Sprint 3 tests עבור עובדים, אילוצים וסידור עבודה.

אזורים מרכזיים שנבדקים:

* Signup / login / forgot password / profile.
* Pepper varieties.
* Tour booking legacy routes, payment records, my booked tours and cancellation.
* Website feedback and tour reviews.
* Admin dashboard and admin permissions.
* Job applications.
* Notifications.
* Worker dashboard.
* Worker constraints.
* Weekly schedule save/publish/reset.
* Closed days.
* Employee attendance.

CI/CD:

הקובץ `.github/workflows/CI.yml` רץ על push/PR ל-`main` או `develop`, וגם ידנית.

Quality gates:

* `python -m compileall backend`
* `flake8 backend --select=E9,F63,F7,F82 --max-line-length=120`
* import smoke test:

```text
python -c "from backend.main import app; print(app.name)"
```

* `pytest backend/tests`
* העלאת JUnit report.
* Deploy ל-Azure Web App אחרי הצלחת quality-check בתנאים שהוגדרו.

לתיעוד מלא של הבדיקות ראו:

* [documents/TEST_INFO.md](documents/TEST_INFO.md)

## 8. Setup and Run Instructions

### Requirements

מומלץ:

* Python 3.11
* SQL Server / Azure SQL
* SQL Server ODBC Driver:
  * `ODBC Driver 18 for SQL Server`
  * או `ODBC Driver 17 for SQL Server`

תלויות Python נמצאות ב:

```text
requirements.txt
```

### Create virtual environment

Windows / PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux/macOS:

```bash
python -m pip install -r requirements.txt
```

### Environment variables

צרו קובץ `.env` בשורש הפרויקט. אין להעלות אותו ל-Git.

אפשרות connection string מלא:

```env
AZURE_SQL_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:your-server.database.windows.net,1433;DATABASE=your-database;UID=your-user;PWD=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
SECRET_KEY=replace-with-a-long-random-secret
FLASK_DEBUG=true
```

אפשרות משתנים נפרדים:

```env
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database
AZURE_SQL_USERNAME=your-user
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DRIVER=ODBC Driver 18 for SQL Server
AZURE_SQL_TIMEOUT=30
SECRET_KEY=replace-with-a-long-random-secret
FLASK_DEBUG=true
```

אפשרות יצירת מנהל בזמן startup:

```env
INIT_ADMIN_ON_STARTUP=true
ADMIN_FULL_NAME=System Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=replace-with-a-secure-admin-password
```

המערכת תומכת גם ב:

* `ConnectionStrings__MyDbConnection`
* `ConnectionStrings_MyDbConnection`
* `appsettings.json` עם `ConnectionStrings.MyDbConnection`

קובץ דוגמה:

* `appsettings.example.json`

### Run Flask app

Windows:

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

Linux/macOS:

```bash
python backend/main.py
```

Open:

```text
http://127.0.0.1:5000
```

בזמן startup, האפליקציה מנסה ליצור/לעדכן טבלאות דרך:

* `create_tables()`
* `create_employee_tables()`
* `create_worker_constraints_table()`
* `create_employee_schedule_settings_tables()`
* `create_weekly_schedule_tables()`

### Run tests

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
```

Linux/macOS:

```bash
python -m pytest backend/tests
```

Unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\unit
```

Integration tests:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\integration
```

Compile check:

```powershell
.\.venv\Scripts\python.exe -m compileall backend
```

Lint check:

```powershell
.\.venv\Scripts\python.exe -m flake8 backend --select=E9,F63,F7,F82 --max-line-length=120
```

לתיעוד מפורט יותר:

* [documents/SETUP_AND_RUN_GUIDE.md](documents/SETUP_AND_RUN_GUIDE.md)

## 9. Main Data Flows

### Signup/Login Flow

```text
User fills signup/login form
-> Flask route reads form
-> validation/service checks data
-> user is created or loaded from users table
-> password hash is checked/generated
-> session role controls access
-> user is redirected according to role
```

### Tour Booking Flow

```text
Visitor selects tour
-> selects date
-> selects time and participants
-> enters personal details
-> payment confirmation creates booking and payment records
-> notifications are sent
-> user can view booking in My Booked Tours
```

Tables:

* `tour_packages`
* `tour_bookings`
* `payments`
* `notifications`

### Worker Constraints Flow

```text
Worker opens /worker-constraints
-> submits availability form
-> service validates open window, published status, closed days and minimum availability
-> repository saves one submission row
-> repository saves day rows
-> admin sees constraints in weekly schedule page
```

Tables:

* `weekly_schedule_weeks`
* `employee_constraint_submissions`
* `employee_constraint_days`
* `employee_schedule_closed_days`

### Weekly Schedule Flow

```text
Admin opens /admin/weekly-schedule
-> sees workers and submitted constraints
-> assigns workers in the UI
-> JavaScript builds assignments_payload
-> save route sends payload to weekly_schedule_service
-> repository saves/publishes weekly schedule
-> workers see only published schedules
-> reset clears assignments and returns week to draft
```

Tables:

* `weekly_schedule_weeks`
* `weekly_schedule_assignments`

### Job Application Flow

```text
Visitor submits job application
-> row is saved in job_applications
-> admin reviews in dashboard
-> approval updates existing registered user's role to employee
-> notification is sent
```

Tables:

* `job_applications`
* `users`
* `roles`
* `notifications`

## 10. Project Defense Notes

מטרת המערכת:

* לבנות פלטפורמה דיגיטלית לחוות פלפלים שמנהלת גם את חוויית המבקר וגם את העבודה הפנימית.

מה מומש:

* אתר ציבורי.
* הרשמה והתחברות.
* ניהול פלפלים.
* ניהול והזמנת סיורים.
* תשלומים פנימיים.
* משובים ודירוגים.
* דשבורד מנהל.
* מועמדויות עבודה.
* התראות.
* דשבורד עובד.
* אילוצי עובדים וסידור עבודה שבועי.

מה Sprint 3 הוסיף:

* תהליך תפעולי של עובד -> אילוצים -> מנהל -> שיבוץ -> פרסום -> עובד רואה סידור.

האתגר הטכני המרכזי:

* חיבור בין UI, routes, services, repositories וטבלאות SQL תוך שמירה על הרשאות וחוקים עסקיים כמו חלון אילוצים, מינימום זמינות ו-published-only לעובדים.

מה ניתן לשפר בעתיד:

* אוטומציה של בניית סידור.
* סליקה אמיתית.
* בדיקות E2E.
* איחוד מסלולים ישנים וחדשים.

## 11. Future Improvements / Known Limitations

מגבלות אמיתיות לפי הקוד הנוכחי:

* Automatic schedule generation from constraints is not implemented; admin assigns workers manually.
* External payment provider is not implemented; `payments` stores internal payment records only.
* CV file upload is not implemented; job applications store text experience only.
* Browser E2E tests are not implemented.
* Worker assigned tours are partially implemented; assignment is basic and based on available employee shifts.
* Multiple older/legacy tour booking pages still exist alongside the newer multi-step flow.
* Older `employee_shifts` logic exists alongside the newer `weekly_schedule_assignments` weekly schedule logic.
* Some placeholder/unconnected templates exist, such as `worker_details.html` and `employee_tours.html`.
* `backend/main.py` is large and could be split into Blueprints in the future.

## 12. Documentation Files

Current documentation files:

* [documents/DATABASE.md](documents/DATABASE.md) - database tables, purpose, columns, CRUD usage and data flow.
* [documents/UI.md](documents/UI.md) - UI pages, routes, permissions, actions and status.
* [documents/FOR_ME.md](documents/FOR_ME.md) - personal Hebrew explanation for understanding the full implementation before defense.
* [documents/TEST_INFO.md](documents/TEST_INFO.md) - existing tests, test functions, quality checks and coverage gaps.
* [documents/PROJECT_IMPLEMENTATION_SUMMARY.md](documents/PROJECT_IMPLEMENTATION_SUMMARY.md) - full current implementation summary by roles, sprints, services and repositories.
* [documents/SPRINT3_IMPLEMENTATION_SUMMARY.md](documents/SPRINT3_IMPLEMENTATION_SUMMARY.md) - detailed Sprint 3 implementation summary.
* [documents/SETUP_AND_RUN_GUIDE.md](documents/SETUP_AND_RUN_GUIDE.md) - setup, environment variables, run commands and troubleshooting.
* [documents/DEFENSE_GUIDE.md](documents/DEFENSE_GUIDE.md) - short preparation guide for the project defense.

## Notes

Security reminders:

* Do not commit `.env`.
* Do not commit real `appsettings.json`.
* Store only password hashes.
* Use Azure Application Settings for production secrets.

Status note:

* This README describes the current implementation in this workspace after the documentation cleanup.
