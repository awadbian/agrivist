# מדריך התקנה והרצה של AgriVisit

מסמך זה מסביר איך להריץ את פרויקט AgriVisit מקומית, איך להגדיר את החיבור למסד הנתונים, ואיך להריץ בדיקות.

## דרישות מערכת

נדרש:

* Python 3.11 מומלץ. גם Python 3.12 עשוי לעבוד אם כל התלויות מותקנות.
* סביבת Windows / PowerShell או סביבת פיתוח שתומכת ב-Python.
* SQL Server או Azure SQL.
* ODBC Driver for SQL Server, בדרך כלל:
  * `ODBC Driver 18 for SQL Server`
  * או `ODBC Driver 17 for SQL Server`
* קובץ `requirements.txt` מהפרויקט.

## מבנה הפרויקט

```text
backend/
  main.py
  service/
  data_access/
  domain/
  tests/

frontend/
  templates/
  static/

documents/
requirements.txt
README.md
.env
appsettings.example.json
```

## יצירת סביבת עבודה

אם אין סביבת virtual environment:

```powershell
python -m venv .venv
```

הפעלה:

```powershell
.\.venv\Scripts\Activate.ps1
```

אם יש בעיית הרשאות PowerShell, ניתן להריץ:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## התקנת תלויות

מהשורש של הפרויקט:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

אם הסביבה כבר פעילה:

```powershell
pip install -r requirements.txt
```

## משתני סביבה

יש ליצור קובץ `.env` בשורש הפרויקט. אין להעלות קובץ זה ל-Git.

אפשרות 1 - connection string מלא:

```env
AZURE_SQL_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:your-server.database.windows.net,1433;DATABASE=your-database;UID=your-user;PWD=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
SECRET_KEY=replace-with-a-long-random-secret
FLASK_DEBUG=true
INIT_ADMIN_ON_STARTUP=false
ADMIN_FULL_NAME=System Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=replace-with-a-secure-admin-password
```

אפשרות 2 - משתנים נפרדים:

```env
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database
AZURE_SQL_USERNAME=your-user
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DRIVER=ODBC Driver 18 for SQL Server
AZURE_SQL_TIMEOUT=30
SECRET_KEY=replace-with-a-long-random-secret
FLASK_DEBUG=true
INIT_ADMIN_ON_STARTUP=false
ADMIN_FULL_NAME=System Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=replace-with-a-secure-admin-password
```

המערכת תומכת גם ב:

* `ConnectionStrings__MyDbConnection`
* `ConnectionStrings_MyDbConnection`
* `appsettings.json` עם `ConnectionStrings.MyDbConnection`

קובץ דוגמה קיים:

* `appsettings.example.json`

## הרצת האפליקציה

מהשורש של הפרויקט:

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

ואז לפתוח בדפדפן:

```text
http://127.0.0.1:5000
```

בזמן העלייה, `backend/main.py` מנסה להפעיל יצירת טבלאות:

* `create_tables()`
* `create_employee_tables()`
* `create_worker_constraints_table()`
* `create_weekly_schedule_tables()`
* `create_employee_schedule_settings_tables()`

אם אין חיבור למסד הנתונים, חלק מהעמודים שמבוססים על DB עלולים להיכשל או להציג מידע חסר.

## יצירת מנהל אוטומטית

אפשר להגדיר יצירת מנהל בזמן עליית המערכת:

```env
INIT_ADMIN_ON_STARTUP=true
ADMIN_FULL_NAME=System Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=replace-with-a-secure-admin-password
```

התנהגות:

* אם המשתמש לא קיים, המערכת יוצרת אותו כמנהל.
* אם המשתמש כבר קיים, המערכת מעדכנת אותו לתפקיד admin ומעדכנת סיסמה.

## בדיקת חיבור למסד הנתונים

קיים כלי בדיקה:

```powershell
.\.venv\Scripts\python.exe backend\tests\db_test.py
```

עם אתחול טבלאות:

```powershell
.\.venv\Scripts\python.exe backend\tests\db_test.py --init
```

## הרצת בדיקות

כל הבדיקות:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
```

בדיקות Unit בלבד:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\unit
```

בדיקות Integration בלבד:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\integration
```

בדיקות Sprint 3 מרכזיות:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\unit\test_worker_constraints_service.py backend\tests\unit\test_weekly_schedule_service.py backend\tests\integration\test_worker_attendance.py backend\tests\integration\test_admin.py
```

## בדיקת קומפילציה ו-Lint

קומפילציה:

```powershell
.\.venv\Scripts\python.exe -m compileall backend
```

בדיקת flake8 כמו ב-CI:

```powershell
.\.venv\Scripts\python.exe -m flake8 backend --select=E9,F63,F7,F82 --max-line-length=120
```

## CI/CD

קובץ workflow:

* `.github/workflows/CI.yml`

השלבים:

* Checkout.
* התקנת Python 3.11.
* התקנת dependencies.
* קומפילציה עם `compileall`.
* בדיקת flake8 קריטית.
* smoke test של import לאפליקציה.
* הרצת pytest.
* העלאת דוח JUnit.
* Deploy ל-Azure Web App רק אחרי הצלחת בדיקות ובתנאים שהוגדרו.

## Routes חשובים לבדיקה ידנית

Public:

* `/`
* `/about`
* `/pepper-varieties`
* `/tours`

Authentication:

* `/signup`
* `/login`
* `/logout`
* `/profile`
* `/forgot-password`

Tours:

* `/tours/calendar/<id>`
* `/tours/time/<id>`
* `/tours/details`
* `/tours/payment`
* `/my-booked-tours`

Admin:

* `/admin-dashboard`
* `/admin/add-pepper`
* `/admin/add-tour`
* `/admin/weekly-schedule`

Worker:

* `/worker-dashboard`
* `/worker-constraints`
* `/worker-tours`
* `/employee-schedule`
* `/shift-status`
* `/weekly-shift-calendar`

## בעיות נפוצות

### אין חיבור למסד נתונים

בדיקות:

* לוודא שקובץ `.env` נמצא בשורש הפרויקט.
* לוודא ששם השרת, בסיס הנתונים, המשתמש והסיסמה נכונים.
* לוודא ש-ODBC Driver מותקן.
* לוודא ש-Azure SQL מאפשר חיבור מהמחשב.

### שגיאת ODBC Driver

פתרון:

* להתקין `ODBC Driver 18 for SQL Server`.
* או להגדיר `AZURE_SQL_DRIVER=ODBC Driver 17 for SQL Server` אם זו הגרסה שמותקנת.

### Templates לא נמצאים

לוודא שהתבניות נמצאות ב:

```text
frontend/templates/
```

וש-`backend/main.py` מגדיר את Flask עם:

```text
template_folder = frontend/templates
static_folder = frontend/static
```

### Static files או תמונות לא נטענות

לוודא שהקבצים נמצאים ב:

```text
frontend/static/
```

ובתבניות משתמשים ב:

```jinja
{{ url_for('static', filename='...') }}
```

### פורט 5000 תפוס

אפשר לסגור את התהליך שתופס את הפורט או להריץ את Flask על פורט אחר על ידי שינוי זמני של `app.run` בזמן פיתוח.

### בדיקות לא מוצאות imports

להריץ בדיקות משורש הפרויקט:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
```

## הערות אבטחה

* לא להעלות `.env`.
* לא להעלות `appsettings.json` אמיתי עם סודות.
* להשתמש בסיסמה חזקה ל-`SECRET_KEY`.
* סיסמאות משתמשים נשמרות כ-hash.
* בפריסה ל-Azure יש להגדיר סודות דרך Application Settings.

## פקודות מהירות

| פעולה | פקודה |
| --- | --- |
| התקנת תלויות | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| הרצת האפליקציה | `.\.venv\Scripts\python.exe backend\main.py` |
| בדיקות | `.\.venv\Scripts\python.exe -m pytest backend\tests` |
| בדיקות Unit | `.\.venv\Scripts\python.exe -m pytest backend\tests\unit` |
| קומפילציה | `.\.venv\Scripts\python.exe -m compileall backend` |
| Lint | `.\.venv\Scripts\python.exe -m flake8 backend --select=E9,F63,F7,F82 --max-line-length=120` |
| בדיקת DB | `.\.venv\Scripts\python.exe backend\tests\db_test.py` |

