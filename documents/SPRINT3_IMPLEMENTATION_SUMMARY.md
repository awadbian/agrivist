# סיכום מימוש Sprint 3

מסמך זה מתמקד במימוש Sprint 3 בפרויקט AgriVisit לפי הקוד הנוכחי. המטרה היא להסביר בצורה ברורה את חלק העובדים, האילוצים וסידור העבודה השבועי.

## מטרת Sprint 3

Sprint 3 מוסיף למערכת יכולות תפעוליות עבור עובדים ומנהלים:

* עובד יכול לראות את סידור העבודה שלו.
* עובד יכול להגיש אילוצים לשבוע עבודה.
* מנהל יכול לראות מי הגיש אילוצים.
* מנהל יכול לשבץ עובדים למשמרות.
* מנהל יכול לשמור, לפרסם או לאפס סידור עבודה.
* מנהל יכול לפתוח או לסגור את חלון עדכון האילוצים.
* המערכת מציגה לעובדים רק סידור שפורסם.

## קבצים מרכזיים ב-Sprint 3

Routes:

* `backend/main.py`

Services:

* `backend/service/worker_constraints_service.py`
* `backend/service/weekly_schedule_service.py`

Repositories:

* `backend/data_access/worker_constraints_repository.py`
* `backend/data_access/weekly_schedule_repository.py`
* `backend/data_access/employee_repository.py`
* `backend/data_access/employee_schedule_settings_repository.py`
* `backend/data_access/job_application_data_access.py`
* `backend/data_access/notification_repository.py`

Templates:

* `frontend/templates/worker_dashboard.html`
* `frontend/templates/worker_constraints.html`
* `frontend/templates/worker_tours.html`
* `frontend/templates/employee_schedule.html`
* `frontend/templates/weekly_shift_calendar.html`
* `frontend/templates/shift_status.html`
* `frontend/templates/admin/weekly_schedule.html`
* `frontend/templates/work_planning.html`
* `frontend/templates/work_planning_employee.html`
* `frontend/templates/job_application.html`

## דשבורד עובד

Route:

* `GET /worker-dashboard`

מטרה:
להציג לעובד תמונת מצב קצרה על העבודה שלו: המשמרת הבאה, מספר משמרות, שעות שבועיות, שעות חודשיות וסידור שבועי שפורסם.

זרימת נתונים:

```text
worker_dashboard.html
<- /worker-dashboard
<- load_active_published_schedule()
<- weekly_schedule_repository
<- weekly_schedule_weeks + weekly_schedule_assignments
```

מה העובד רואה:

* שם העובד.
* המשמרת הבאה.
* מספר משמרות.
* שעות שבועיות.
* שעות חודשיות.
* טבלת סידור עבודה שבועי שפורסם.
* קישורים לאילוצים, סיורים, סידור עבודה וסטטוס משמרת.

הרשאות:

* רק `employee`.
* משתמש לא עובד מופנה לדף הבית.

טבלאות:

* `weekly_schedule_weeks`
* `weekly_schedule_assignments`

הערה:
הדשבורד לא שומר נתונים בעצמו. הנתונים מחושבים מתוך הסידור שפורסם.

## סידור שבועי לעובד

Route:

* `GET /employee-schedule`

מטרה:
להציג לעובד את המשמרות שלו בשבוע שנבחר.

מה מיושם:

* עובד רואה רק את עצמו.
* מנהל יכול לראות עובד מסוים אם נבחר מצב צפייה כעובד.
* מנהל רגיל יכול לראות עובדים.
* מוצגים רק שיבוצים מתוך סידור שפורסם.

זרימת נתונים:

```text
/employee-schedule
-> get_employee_by_email()
-> load_employee_published_schedule()
-> get_published_assignments_for_employee()
-> weekly_schedule_assignments
-> employee_schedule.html
```

טבלאות:

* `employee_profiles`
* `employee_shifts`
* `weekly_schedule_weeks`
* `weekly_schedule_assignments`

כלל חשוב:
סידור במצב draft לא מוצג לעובדים.

## הגשת אילוצים לעובד

Route:

* `GET /worker-constraints`
* `POST /worker-constraints`

מטרה:
לאפשר לעובד להגיש זמינות לשבוע עבודה פעיל.

אפשרויות זמינות:

* `morning`: בוקר
* `evening`: ערב
* `all_day`: זמין כל היום
* `unavailable`: לא זמין
* `midday`: נתמך כערך legacy

כללים:

* רק עובד יכול לגשת לעמוד.
* חייב להיות שבוע אילוצים פתוח.
* אי אפשר להגיש אילוצים לשבוע שכבר פורסם לו סידור.
* אי אפשר להגיש אם המנהל סגר את חלון האילוצים.
* יש לבחור ערך לכל יום עבודה.
* חייבים לבחור לפחות 4 ימים זמינים.
* שבת לא חלק מהטופס.
* ביום שישי מותר רק בוקר או לא זמין.
* יום שסומן כסגור על ידי מנהל הופך לבלתי זמין.

זרימת GET:

```text
/worker-constraints
-> get_existing_constraints(employee_email)
-> get_open_constraints_week()
-> get_worker_constraints()
-> get_closed_constraint_days()
-> worker_constraints.html
```

זרימת POST:

```text
worker_constraints.html form
-> /worker-constraints
-> submit_worker_constraints()
-> normalize_constraints_submission()
-> save_worker_constraints()
-> employee_constraint_submissions
-> employee_constraint_days
-> redirect summary
```

טבלאות:

* `weekly_schedule_weeks`: קובע איזה שבוע פתוח לאילוצים.
* `employee_constraint_submissions`: רשומת ההגשה הראשית.
* `employee_constraint_days`: זמינות לכל יום.
* `employee_schedule_closed_days`: ימים סגורים.

מצב עריכה:
אם חלון האילוצים פתוח ויש כבר הגשה, העובד יכול לערוך ולעדכן אותה.

## עמוד מנהל לסידור עבודה שבועי

Route:

* `GET /admin/weekly-schedule`

Template:

* `frontend/templates/admin/weekly_schedule.html`

מטרה:
לאפשר למנהל לבנות סידור עבודה לשבוע, על בסיס עובדים ואילוצים שהוגשו.

מה העמוד מציג:

* בחירת שבוע להצגה.
* תאריכי השבוע.
* סטטוס הסידור: טיוטה / פורסם / טרם נשמר.
* סטטוס חלון האילוצים: פתוח / סגור.
* עובדים וזמינות לפי אילוצים.
* סטטוס מי הגיש ומי לא הגיש אילוצים.
* לוח שיבוץ לפי ימים ומשמרות.
* טבלת סידור שמור אם קיימים שיבוצים.
* כפתורי שמירה, איפוס, פתיחת/סגירת אילוצים וסימון יום סגור.

בחירת שבוע:

* המערכת משתמשת ב-`MAX_WEEK_OFFSET = 2`.
* כלומר מנהל יכול לבחור עד שני שבועות קדימה.
* ערך קטן מ-1 מתוקן ל-1.
* ערך גדול מ-2 מתוקן ל-2.

זרימת נתונים:

```text
/admin/weekly-schedule
-> normalize_week_offset()
-> week_start_for_offset()
-> load_employees_from_db()
-> get_worker_constraint_submissions_for_week()
-> get_closed_days_for_week()
-> get_weekly_schedule_week()
-> get_weekly_schedule_assignments()
-> admin/weekly_schedule.html
```

טבלאות:

* `employee_profiles`
* `employee_constraint_submissions`
* `employee_constraint_days`
* `employee_schedule_closed_days`
* `weekly_schedule_weeks`
* `weekly_schedule_assignments`

## שמירת ופרסום סידור עבודה

Route:

* `POST /admin/weekly-schedule/save`

מטרה:
לשמור את השיבוצים שהמנהל בנה ולפרסם אותם לעובדים.

איך זה עובד:

* ה-Template בונה JSON בשם `assignments_payload`.
* ה-Route מעביר את ה-JSON ל-`save_weekly_schedule_draft_from_payload`.
* השירות מפענח את ה-JSON.
* השירות מסנן שיבוצים לא תקינים.
* ה-Repository שומר את השבוע והשיבוצים.
* כרגע השמירה נעשית עם `publish=True`, כלומר הסידור נשמר ומפורסם באותה פעולה.

זרימת נתונים:

```text
admin/weekly_schedule.html
-> assignments_payload
-> /admin/weekly-schedule/save
-> save_weekly_schedule_draft_from_payload(..., publish=True)
-> save_weekly_schedule_draft()
-> weekly_schedule_weeks
-> weekly_schedule_assignments
```

מה נשמר:

* שבוע העבודה.
* סטטוס published.
* תאריך פרסום.
* כל שיבוץ עובד למשמרת.

כללים:

* שבת לא נשמרת.
* שישי ערב לא נשמר.
* שיבוץ חסר עובד/יום/משמרת/תאריך מסונן.
* לאחר פרסום, חלון האילוצים של אותו שבוע נסגר.
* לאחר פרסום, נפתח חלון אילוצים לשבוע הבא.

## פרסום סידור עבודה קיים

Route:

* `POST /admin/weekly-schedule/publish`

מטרה:
לפרסם סידור שכבר נשמר.

הערה:
בקוד קיימת יכולת לפרסום סידור קיים, אבל בזרימת הממשק הנוכחית כפתור השמירה המרכזי כבר שומר ומפרסם יחד.

טבלאות:

* `weekly_schedule_weeks`
* `weekly_schedule_assignments`

## איפוס סידור עבודה

Route:

* `POST /admin/weekly-schedule/reset`

מטרה:
לאפס את השיבוצים של השבוע שנבחר.

מה קורה:

* נמחקים שיבוצים מ-`weekly_schedule_assignments`.
* רשומת השבוע נשארת.
* סטטוס השבוע מתעדכן ל-draft.
* `published_at` מתאפס.
* חלון האילוצים הפעיל לא משתנה.

זרימת נתונים:

```text
/admin/weekly-schedule/reset
-> reset_weekly_schedule_draft()
-> delete_weekly_schedule_draft()
-> weekly_schedule_assignments delete
-> weekly_schedule_weeks update
```

## פתיחה וסגירה של חלון אילוצים

Route:

* `POST /admin/weekly-schedule/submission-window`

מטרה:
לאפשר למנהל לשלוט מתי עובדים יכולים להגיש או לערוך אילוצים.

פתיחה:

```text
is_open = 1
-> open_constraints_for_week()
-> סוגר שבועות אחרים שפתוחים
-> פותח את השבוע הנבחר
```

סגירה:

```text
is_open = 0
-> set_constraints_status_for_week(..., closed)
```

כלל חשוב:
אי אפשר לפתוח אילוצים לשבוע שכבר פורסם לו סידור עבודה.

טבלה:

* `weekly_schedule_weeks.constraints_status`

## ימים סגורים

Route:

* `POST /admin/weekly-schedule/closed-day`

מטרה:
לאפשר למנהל לסמן יום מסוים כסגור.

השפעה:

* יום סגור לא מציג משמרות בלוח השיבוץ.
* יום סגור בטופס אילוצים נחשב לא זמין.

טבלה:

* `employee_schedule_closed_days`

זרימה:

```text
/admin/weekly-schedule/closed-day
-> set_closed_day()
-> employee_schedule_closed_days
-> reload weekly schedule page
```

## איפוס אילוצים

Route:

* `POST /admin/weekly-schedule/reset-constraints`

מטרה:
למחוק את כל אילוצי העובדים לשבוע שנבחר.

טבלאות:

* `employee_constraint_submissions`
* `employee_constraint_days`

זרימה:

```text
/admin/weekly-schedule/reset-constraints
-> delete_worker_constraints_for_week()
-> delete days
-> delete submissions
```

## סיורים משויכים לעובד

Route:

* `GET /worker-tours`

מטרה:
להציג לעובד את הזמנות הסיור ששויכו אליו.

איך עובד השיוך:

* בזמן יצירת הזמנה, `find_available_worker_id` מחפש עובד זמין לפי `employee_shifts`.
* אם נמצא עובד מתאים, נשמר `assigned_worker_id` בתוך `tour_bookings`.
* העובד רואה הזמנות שבהן `assigned_worker_id` שווה ל-`session["user_id"]`.

טבלאות:

* `tour_bookings`
* `employee_shifts`
* `users`

הערה:
זה מימוש בסיסי. אין עדיין מערכת שיבוץ סיורים מתקדמת לפי עומסים או אילוצים.

## בקשות עבודה

Routes:

* `GET /job-application`
* `POST /job-application`
* `POST /admin/job-applications/<id>/approve`
* `POST /admin/job-applications/<id>/reject`

מטרה:
לאפשר למבקר להגיש מועמדות לעבודה ולמנהל לאשר או לדחות.

מה ממומש:

* טופס מועמדות.
* שמירת בקשה בסטטוס pending.
* הצגת בקשות בדשבורד מנהל.
* אישור מועמד אם הוא כבר משתמש רשום.
* שינוי תפקיד המשתמש ל-employee.
* שליחת התראה למועמד.
* דחיית מועמד.

טבלאות:

* `job_applications`
* `users`
* `roles`
* `notifications`

הערה:
אין העלאת קובץ CV. השדה `experience` הוא טקסט חופשי.

## נוכחות וסטטוס משמרת

Routes:

* `GET /weekly-shift-calendar`
* `GET /shift-status`
* `POST /start-shift`
* `POST /end-shift`

מטרה:
לאפשר לעובד להתחיל ולסיים משמרת, ולהציג שעות ושכר.

טבלאות:

* `employee_attendance`
* `employee_profiles`

מה נשמר:

* תאריך עבודה.
* שעת התחלה.
* שעת סיום.
* שעות עבודה.
* שכר יומי.
* האם העובד עדיין במשמרת.

הערה:
קיים גם קובץ `backend/employee_attendance.json`, אבל הקריאה הנוכחית לנתוני נוכחות משתמשת ב-Repository של בסיס הנתונים.

## בדיקות שמכסות Sprint 3

קבצים מרכזיים:

* `backend/tests/unit/test_worker_constraints_service.py`
* `backend/tests/unit/test_worker_constraints_repository.py`
* `backend/tests/unit/test_weekly_schedule_service.py`
* `backend/tests/unit/test_weekly_schedule_repository.py`
* `backend/tests/unit/test_employee_schedule_settings_repository.py`
* `backend/tests/integration/test_worker_attendance.py`
* `backend/tests/integration/test_admin.py`
* `backend/tests/integration/test_job_application.py`
* `backend/tests/integration/test_admin_job_applications.py`

מה נבדק:

* גישה לפי תפקיד.
* טופס אילוצים פתוח/סגור.
* מינימום 4 ימים זמינים.
* שישי בלי משמרת ערב.
* עובדים לא רואים draft.
* מנהל יכול לפתוח/לסגור אילוצים.
* מנהל יכול לשמור, לפרסם ולאפס סידור.
* בחירת שבוע מוגבלת לשני שבועות.
* בקשות עבודה ואישור מועמד.

## סיכום Sprint 3 להגנה

Sprint 3 הוסיף את החלק התפעולי של המערכת:

* עובד מגיש אילוצים.
* מנהל רואה אילוצים ובונה סידור.
* סידור עבודה נשמר בבסיס הנתונים.
* עובדים רואים רק סידור שפורסם.
* המנהל שולט בחלון הגשת האילוצים.
* המערכת תומכת גם בבקשות עבודה ובהפיכת מבקר לעובד.

התרומה המרכזית היא חיבור בין UI, routes, service, repository ובסיס הנתונים כדי לנהל תהליך עבודה שבועי מלא.

