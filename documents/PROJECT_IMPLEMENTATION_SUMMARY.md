# סיכום מימוש הפרויקט AgriVisit

מסמך זה מסכם את המימוש הנוכחי של AgriVisit לפי הקוד הקיים בפרויקט. הוא מיועד להכנה להגנה ולהבנת המערכת לפני עדכון מסמכי הפרויקט.

## מטרת הפרויקט

AgriVisit היא פלטפורמה דיגיטלית למרכז מבקרים חקלאי / חוות פלפלים.

המערכת תומכת בשלושה קהלי יעד מרכזיים:

* מבקרים באתר: צפייה במידע, הרשמה, הזמנת סיורים, משוב ודירוגים.
* עובדים: צפייה בסידור עבודה, הגשת אילוצים, צפייה בסיורים משויכים וניהול סטטוס משמרת.
* מנהלים: ניהול משתמשים, פלפלים, סיורים, הזמנות, תשלומים, מועמדויות וסידור עבודה שבועי.

## מבנה כללי של הפרויקט

הפרויקט בנוי כאפליקציית Flask עם הפרדה בין Backend ו-Frontend.

תיקיות מרכזיות:

* `backend/main.py`: קובץ ה-Flask הראשי, כולל routes, בדיקות session והרצת האפליקציה.
* `backend/service/`: שכבת שירותים וחוקים עסקיים.
* `backend/data_access/`: שכבת גישה למסד הנתונים.
* `backend/domain/`: אובייקטי מידע פשוטים כמו User, Pepper ו-Tour.
* `frontend/templates/`: תבניות HTML של Jinja.
* `frontend/static/`: קבצי CSS, JavaScript ותמונות.
* `backend/tests/`: בדיקות unit ו-integration.
* `documents/`: מסמכי תיעוד.

זרימת בקשה כללית:

```text
Browser / Form
-> backend/main.py route
-> backend/service
-> backend/data_access repository
-> SQL Server / Azure SQL
-> render_template
-> HTML response
```

## תפקידי משתמשים

### מבקר / Visitor

מה המבקר יכול לעשות:

* להירשם ולהתחבר.
* לעדכן פרופיל.
* לצפות בדף הבית, אודות, זני פלפלים וסיורים.
* להזמין סיור ולשלם בתיעוד פנימי של המערכת.
* לצפות בהזמנות שלו ולבטל הזמנה אם נשארו לפחות יומיים.
* לשלוח משוב על האתר.
* לדרג סיור אחרי הזמנה מתאימה.
* להגיש מועמדות לעבודה.

Routes עיקריים:

* `/signup`
* `/login`
* `/profile`
* `/pepper-varieties`
* `/tours`
* `/tours/calendar/<id>`
* `/tours/time/<id>`
* `/tours/details`
* `/tours/payment`
* `/my-booked-tours`
* `/website-feedback`
* `/post-tour-review`
* `/job-application`

### עובד / Employee

מה העובד יכול לעשות:

* לצפות בדשבורד עובד.
* לצפות בסידור עבודה שבועי שפורסם.
* להגיש ולעדכן אילוצים כאשר חלון האילוצים פתוח.
* לצפות בסיורים ששויכו אליו.
* להתחיל ולסיים משמרת.
* לצפות בהתראות.
* לצפות במפת החווה.

Routes עיקריים:

* `/worker-dashboard`
* `/worker-constraints`
* `/worker-tours`
* `/employee-schedule`
* `/weekly-shift-calendar`
* `/shift-status`
* `/start-shift`
* `/end-shift`
* `/notifications`
* `/farm-map`

### מנהל / Admin

מה המנהל יכול לעשות:

* לצפות בדשבורד ניהול.
* לנהל משתמשים פעילים/לא פעילים.
* לנהל זני פלפלים.
* לנהל סיורים.
* לצפות בהזמנות ותשלומים.
* לבטל הזמנות.
* לאשר או לדחות בקשות עבודה.
* לבנות סידור עבודה שבועי.
* לפתוח או לסגור חלון אילוצים.
* לסמן ימים סגורים.
* לאפס אילוצים או סידור עבודה.

Routes עיקריים:

* `/admin-dashboard`
* `/admin/add-pepper`
* `/admin/peppers/<id>/edit`
* `/admin/peppers/<id>/delete`
* `/admin/add-tour`
* `/admin/tours/<id>/edit`
* `/admin/tours/<id>/delete`
* `/admin/weekly-schedule`
* `/admin/weekly-schedule/save`
* `/admin/weekly-schedule/reset`
* `/admin/weekly-schedule/publish`
* `/admin/weekly-schedule/submission-window`
* `/admin/weekly-schedule/closed-day`
* `/admin/job-applications/<id>/approve`
* `/admin/job-applications/<id>/reject`

## Sprint 1 - בסיס המערכת

### הרשמה, התחברות ופרופיל

קבצים מרכזיים:

* `backend/main.py`
* `backend/service/signup_validation.py`
* `backend/data_access/user_repository.py`
* `backend/data_access/role_repository.py`
* `frontend/templates/signup.html`
* `frontend/templates/login.html`
* `frontend/templates/profile.html`

מה ממומש:

* הרשמת משתמש חדש בתפקיד visitor.
* התחברות עם אימייל וסיסמה מוצפנת.
* שמירת session עם `user_id`, `user`, `email`, `role`.
* עדכון פרופיל.
* מחיקת חשבון.
* איפוס סיסמה דרך `/forgot-password`.

חוקים:

* שם מלא חובה.
* אימייל חובה ובפורמט תקין.
* סיסמה באורך 8 תווים לפחות.
* אימות סיסמה חייב להתאים.
* אישור תנאי שימוש חובה.
* אימייל כפול נחסם.

### עמודי תוכן בסיסיים

Routes:

* `/`
* `/about`
* `/farm-map`

מה ממומש:

* דף בית.
* דף אודות.
* מפת חווה לעובדים ומנהלים בלבד.

### זני פלפלים

קבצים מרכזיים:

* `backend/service/pepper_service.py`
* `backend/data_access/pepper_repository.py`
* `backend/data_access/heat_level_repository.py`
* `frontend/templates/pepper_varieties.html`
* `frontend/templates/add_pepper.html`
* `frontend/static/js/pepper-varieties.js`
* `frontend/static/css/pepper-varieties.css`

מה ממומש:

* הצגת זני פלפלים.
* סינון לפי רמות חריפות.
* חיפוש בצד הלקוח.
* מודל פרטים.
* הוספה, עריכה ומחיקה על ידי מנהל.

טבלאות:

* `peppers`
* `pepper_heat_levels`

חוקים:

* מנהל בלבד יכול להוסיף/לערוך/למחוק.
* רמת חריפות יכולה להיקבע לפי Scoville או לפי בחירה 0-5.
* שדות חובה כוללים שם, שם מדעי, ארץ מקור, צבע ותיאור.

## Sprint 2 - סיורים, הזמנות ומשוב

### ניהול סיורים

קבצים מרכזיים:

* `backend/service/tour_service.py`
* `backend/data_access/tour_repository.py`
* `frontend/templates/tours.html`
* `frontend/templates/admin/add_tour.html`
* `frontend/templates/admin/edit_tour.html`

מה ממומש:

* הצגת סיורים פעילים.
* הוספת סיור על ידי מנהל.
* עריכת סיור.
* מחיקת סיור אם אין הזמנות פעילות.
* העלאת תמונת סיור לתיקיית `frontend/static/images/tours`.

טבלה:

* `tour_packages`

חוקים:

* מחיר, משך ומספר משתתפים חייבים להיות מספרים חיוביים.
* תאריך סיום זמינות חייב להיות אחרי תאריך התחלה.
* מחיקה נחסמת אם קיימות הזמנות פעילות לסיור.

### הזמנת סיור

קבצים מרכזיים:

* `backend/main.py`
* `backend/data_access/tour_booking_repository.py`
* `frontend/templates/tour_calendar.html`
* `frontend/templates/tour_time.html`
* `frontend/templates/tour_details.html`
* `frontend/templates/tour_payment.html`
* `frontend/templates/my_booked_tours.html`

מה ממומש:

* בחירת סיור.
* בחירת תאריך.
* בחירת שעה ומספר משתתפים.
* הכנסת פרטי מבקר.
* אישור תשלום.
* שמירת הזמנה.
* הצגת הזמנות למשתמש.
* ביטול הזמנה בתנאי שיש לפחות יומיים עד הסיור.

טבלאות:

* `tour_bookings`
* `payments`

חוקים:

* אי אפשר לבחור תאריך שעבר.
* מספר משתתפים חייב להיות חיובי ולא לעבור את `max_people`.
* אימייל ההזמנה חייב להיות האימייל של המשתמש המחובר.
* ביטול משתמש מותר רק לפחות יומיים לפני הסיור.

### משוב ודירוגים

קבצים:

* `backend/data_access/tour_rating_repository.py`
* `backend/data_access/website_feedback_repository.py`
* `backend/data_access/satisfaction_repository.py`
* `frontend/templates/website_feedback.html`
* `frontend/templates/post_tour_review.html`

מה ממומש:

* משוב כללי על האתר.
* דירוג סיור לאחר הזמנה מתאימה.
* הצגת דירוגים וסיכומי שביעות רצון.

טבלאות:

* `website_feedback`
* `tour_ratings`

חוקים:

* דירוג חייב להיות בין 1 ל-5.
* לכל הזמנה ניתן לשמור דירוג אחד.

## Sprint 3 - עובדים, אילוצים וסידור עבודה

פירוט מלא נמצא במסמך `SPRINT3_IMPLEMENTATION_SUMMARY.md`.

מימושים מרכזיים:

* דשבורד עובד.
* הגשת אילוצים לעובד.
* סטטוס חלון אילוצים פתוח/סגור.
* עמוד מנהל לסידור עבודה שבועי.
* שיבוץ עובדים למשמרות.
* שמירה ופרסום סידור עבודה.
* איפוס סידור עבודה.
* סימון ימים סגורים.
* צפייה בסידור שפורסם לעובד.
* סיורים משויכים לעובד.
* בקשות עבודה ואישור מועמד לעובד.

טבלאות Sprint 3:

* `employee_profiles`
* `employee_shifts`
* `employee_attendance`
* `employee_constraint_submissions`
* `employee_constraint_days`
* `weekly_schedule_weeks`
* `weekly_schedule_assignments`
* `employee_schedule_closed_days`
* `job_applications`
* `notifications`

## שירותים מרכזיים

* `signup_validation.py`: ולידציית הרשמה.
* `pepper_service.py`: ניהול טפסי פלפלים, סינון, cache ורמות חריפות.
* `tour_service.py`: ניהול טפסי סיורים וולידציה.
* `worker_constraints_service.py`: חישוב שבוע פעיל, ולידציית אילוצים, בדיקת חלון פתוח/סגור.
* `weekly_schedule_service.py`: בניית שבועות, סטטוסי שיבוץ, שמירה/פרסום/איפוס סידור עבודה.
* `admin_service.py`: יצירת/עדכון מנהל מתוך משתני סביבה.

## Repositories מרכזיים

* `db.py`: פתיחת חיבור SQL Server.
* `init_db.py`: יצירת טבלאות בסיס.
* `user_repository.py`: משתמשים ופרופילים.
* `pepper_repository.py`: CRUD של פלפלים.
* `tour_repository.py`: CRUD של חבילות סיור.
* `tour_booking_repository.py`: הזמנות סיור וביטולים.
* `payment_repository.py`: תשלומים.
* `notification_repository.py`: התראות.
* `job_application_data_access.py`: מועמדויות עבודה.
* `worker_constraints_repository.py`: אילוצי עובדים.
* `weekly_schedule_repository.py`: סידור עבודה שבועי.
* `employee_repository.py`: פרופילי עובדים, משמרות ונוכחות.
* `employee_schedule_settings_repository.py`: ימים סגורים.

## תכונות ממומשות במלואן

* הרשמה והתחברות.
* ניהול פרופיל.
* ניהול זני פלפלים.
* הצגת וסינון זני פלפלים.
* ניהול סיורים.
* תהליך הזמנת סיור רב-שלבי.
* תיעוד תשלום פנימי.
* צפייה וביטול הזמנות משתמש.
* משוב ודירוגים.
* התראות לעובדים ומנהלים.
* בקשות עבודה ואישור/דחייה.
* הגשת אילוצים לעובד.
* בניית סידור עבודה שבועי.
* פרסום סידור לעובדים.

## תכונות חלקיות או עתידיות

* אין חיבור אמיתי לספק סליקה חיצוני.
* אין העלאת CV; מועמדות שומרת טקסט ניסיון בלבד.
* אין אלגוריתם אוטומטי מלא שמייצר סידור עבודה מאילוצים; המנהל משבץ ידנית.
* סיורי עובד קיימים, אבל השיוך מבוסס על עובד זמין ראשון לפי `employee_shifts`.
* חלק ממסכי העובד משתמשים גם בתכנון משמרות ישן וגם בסידור עבודה שבועי חדש.
* אין בדיקות Browser E2E מלאות.

## קבצים חשובים להצגה בהגנה

* `backend/main.py`
* `backend/service/worker_constraints_service.py`
* `backend/service/weekly_schedule_service.py`
* `backend/data_access/worker_constraints_repository.py`
* `backend/data_access/weekly_schedule_repository.py`
* `backend/data_access/init_db.py`
* `frontend/templates/admin/weekly_schedule.html`
* `frontend/templates/worker_constraints.html`
* `frontend/templates/worker_dashboard.html`
* `frontend/templates/employee_schedule.html`
* `documents/DATABASE.md`
* `documents/SPRINT3_IMPLEMENTATION_SUMMARY.md`

