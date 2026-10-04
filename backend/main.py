import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.data_access.db import get_connection

from backend.data_access.employee_repository import (
    create_employee_tables,
    seed_employees_if_empty,
    load_employees_from_db,
    get_employee_from_db,
    update_employee_schedule_in_db,
    start_employee_shift_in_db,
    end_employee_shift_in_db,
    get_employee_attendance_from_db,
    sync_employee_profiles_from_users,
)

from backend.data_access.notification_repository import (
    create_notification,
    create_notification_for_all_employees,
    create_notification_for_all_admins,
    get_user_notifications,
    get_unread_notifications_count,
    mark_notification_as_read,
)

from backend.data_access.satisfaction_repository import get_combined_satisfaction_summary

from backend.data_access.tour_rating_repository import (
    get_pending_tour_rating_for_user,
    create_tour_rating,
    get_latest_tour_ratings,
    get_tour_rating_summary,
)

from backend.data_access.website_feedback_repository import (
    create_website_feedback,
    get_latest_website_feedback,
    get_website_feedback_summary,
)

from backend.data_access.worker_constraints_repository import (
    create_worker_constraints_table,
    delete_worker_constraints_for_week,
    get_worker_constraint_submissions_for_week,
    get_worker_constraints,
)
from backend.data_access.employee_schedule_settings_repository import (
    create_employee_schedule_settings_tables,
    set_closed_day,
)
from backend.data_access.weekly_schedule_repository import (
    CONSTRAINTS_STATUS_CLOSED,
    create_weekly_schedule_tables,
    open_constraints_for_week,
    set_constraints_status_for_week,
)
from backend.data_access.payment_repository import create_payment, get_all_payments

from flask import Flask, flash, render_template, request, redirect, url_for, session, abort

from pathlib import Path
from flask import Flask, flash, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from uuid import uuid4
from datetime import date, datetime, timedelta

from backend.data_access.job_application_data_access import (
    create_job_application,
    get_all_job_applications,
    get_job_application_by_id,
    approve_job_application,
    reject_job_application,
)
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.data_access.user_repository import (
    get_registered_users,
    get_farm_workers,
    deactivate_user_by_id,
    activate_user_by_id,
    update_user_role,
    get_user_by_email
)

from backend.data_access.pepper_repository import get_active_peppers_count
from backend.service.signup_validation import validate_signup
from backend.service.pepper_service import (
    create_pepper_from_form,
    delete_pepper,
    empty_pepper_form_data,
    get_pepper_edit_form,
    list_heat_levels,
    list_peppers,
    normalize_pepper_form,
    update_pepper_from_form,
)
from backend.service.tour_service import (
    create_tour_from_form,
    delete_tour as delete_tour_from_service,
    empty_tour_form_data,
    get_active_tour,
    get_tour_edit_form,
    list_active_tours,
    list_admin_tours,
    normalize_tour_form,
    update_tour_from_form,
    get_active_tour,
    
)
from backend.data_access.user_repository import (
    get_user_by_email,
    create_user,
    update_user_password,
    update_user_profile,
    delete_user_by_email 
)
from backend.domain.user import User
from backend.data_access.init_db import create_tables
from backend.service.admin_service import ensure_admin_user
from backend.service.worker_constraints_service import (
    AVAILABILITY_OPTIONS,
    CLOSED_DAY_MESSAGE,
    CONSTRAINT_SUBMISSION_CLOSED_MESSAGE,
    CONSTRAINT_UPDATES_CLOSED_MESSAGE,
    LEGACY_AVAILABILITY_LABELS,
    NO_ACTIVE_CONSTRAINT_WEEK_MESSAGE,
    WORK_DAYS,
    are_constraint_updates_open,
    get_availability_options_by_day,
    get_closed_constraint_days,
    get_existing_constraints,
    submit_worker_constraints,
)
from backend.service.weekly_schedule_service import (
    build_submission_status,
    build_saved_schedule_table,
    build_week_days,
    build_week_options,
    load_employee_published_schedule,
    load_active_constraints_week_context,
    load_active_published_schedule,
    load_employee_monthly_published_schedule,
    load_published_weekly_schedule,
    load_saved_schedule_assignments,
    load_weekly_constraints_status,
    load_weekly_schedule_status,
    load_closed_day_keys,
    normalize_week_offset,
    publish_weekly_schedule_for_employees,
    reset_weekly_schedule_draft,
    save_weekly_schedule_draft_from_payload,
    WORK_WEEK_END_OFFSET_DAYS,
    week_start_for_offset,
)

REAL_WORKER_CONSTRAINTS_SERVICE_MODULE = "backend.service.worker_constraints_service"


def _worker_constraints_updates_open_for_route(week_start_date):
    if (
        app.config.get("TESTING")
        and are_constraint_updates_open.__module__ == REAL_WORKER_CONSTRAINTS_SERVICE_MODULE
        and (
            get_existing_constraints.__module__ != REAL_WORKER_CONSTRAINTS_SERVICE_MODULE
            or submit_worker_constraints.__module__ != REAL_WORKER_CONSTRAINTS_SERVICE_MODULE
        )
    ):
        return True

    return are_constraint_updates_open(week_start_date)

from backend.data_access.tour_booking_repository import (
    create_tour_booking,
    get_all_tour_bookings,
    cancel_tour_booking_by_id,
    has_active_paid_bookings_for_tour,
    get_paid_tour_bookings_by_email,
    cancel_user_tour_booking,
)

app = Flask(
    __name__,
    template_folder=str(ROOT_DIR / "frontend" / "templates"),
    static_folder=str(ROOT_DIR / "frontend" / "static"),
)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-secret-key")
from functools import wraps

def visitor_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") == "employee":
            flash("עובדים רשומים אינם יכולים להגיש מועמדות.", "warning")
            return redirect(url_for("worker_dashboard"))
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return f(*args, **kwargs)
    return decorated_function
TOUR_IMAGE_FOLDER = ROOT_DIR / "frontend" / "static" / "images" / "tours"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def save_tour_image(file):
    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return None

    TOUR_IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)

    new_filename = f"{uuid4().hex}.{extension}"
    file_path = TOUR_IMAGE_FOLDER / new_filename
    file.save(file_path)

    return url_for("static", filename=f"images/tours/{new_filename}")
PEPPER_IMAGE_FOLDER = ROOT_DIR / "frontend" / "static" / "images" / "peppers"

def save_pepper_image(file):
    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return None

    PEPPER_IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)

    new_filename = f"{uuid4().hex}.{extension}"
    file_path = PEPPER_IMAGE_FOLDER / new_filename
    file.save(file_path)

    return url_for("static", filename=f"images/peppers/{new_filename}")

def initialize_database():
    try:
        create_tables()
        create_employee_tables()
        sync_employee_profiles_from_users()
        create_worker_constraints_table()
        create_employee_schedule_settings_tables()
        create_weekly_schedule_tables()
        seed_employees_if_empty()
    except Exception as exc:
        print(f"Warning: database initialization skipped: {exc}")


def initialize_admin():
    try:
        ensure_admin_user()
    except Exception as exc:
        print(f"Warning: admin initialization skipped: {exc}")


# דף ראשי


@app.route("/")
def home():
    pending_review = None

    if session.get("user") and session.get("role") != "admin":
        try:
            pending_review = get_pending_tour_rating_for_user(session.get("email"))
        except Exception as exc:
            print(f"Warning: failed to load pending tour rating: {exc}")

    try:
        website_feedback = get_latest_website_feedback(limit=6)
        website_feedback_summary = get_website_feedback_summary()
    except Exception as exc:
        print(f"Warning: failed to load website feedback: {exc}")
        website_feedback = []
        website_feedback_summary = {
            "average_rating": 0,
            "feedback_count": 0
        }

    return render_template(
        "index.html",
        pending_review=pending_review,
        website_feedback=website_feedback,
        website_feedback_summary=website_feedback_summary,
    )


# דף LOGIN

def ensure_employee_user_account(employee):
    email = employee["email"].strip().lower()
    existing_user = get_user_by_email(email)

    if existing_user:
        if existing_user.get("role") != "employee":
            update_user_role(email, "employee")

        return get_user_by_email(email)

    new_user = User(
        full_name=employee["name"],
        email=email,
        password_hash=generate_password_hash(employee["password"]),
        role="employee"
    )

    create_user(new_user)

    return get_user_by_email(email)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)

        if not user:
            error = "האימייל לא קיים במערכת."
        elif not check_password_hash(user["password_hash"], password):
            error = "הסיסמה שגויה."
        else:
            role_id = user.get("role_id")
            role = "employee" if role_id == 3 else user.get("role", "visitor")

            session["user_id"] = user["id"]
            session["user"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = role

            if role == "employee":
                return redirect(url_for("employee_schedule"))

            return redirect(url_for("home"))

    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    errors = {}
    success = None
    form_data = {
        "full_name": "",
        "email": "",
        "terms": False
    }

    if request.method == "POST":
        form_data["full_name"] = request.form.get("full_name", "").strip()
        form_data["email"] = request.form.get("email", "").strip()
        form_data["terms"] = request.form.get("terms") is not None

        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = validate_signup(
            form_data["full_name"],
            form_data["email"],
            password,
            confirm_password,
            form_data["terms"]
        )

        if not errors:
            existing_user = get_user_by_email(form_data["email"])

            if existing_user:
                errors["email"] = "כתובת האימייל כבר קיימת במערכת."
            else:
                password_hash = generate_password_hash(password)

                new_user = User(
                    full_name=form_data["full_name"],
                    email=form_data["email"],
                    password_hash=password_hash,
                    role="visitor"

                )

                create_user(new_user)
                create_notification_for_all_admins(
                    "משתמש חדש נרשם",
                    f"המשתמש {new_user.full_name} נרשם למערכת עם האימייל {new_user.email}."
                )
                success = "ההרשמה בוצעה בהצלחה!"

                
                form_data = {
                    "full_name": "",
                    "email": "",
                    "terms": False
                }
                session["user"] = new_user.full_name
                session["email"] = new_user.email
                session["role"] = new_user.role
                return redirect(url_for("home"))

    return render_template(
        "signup.html",
        errors=errors,
        success=success,
        form_data=form_data
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user"):
        return redirect(url_for("login"))

    email = session.get("email")
    role = session.get("role")

    if not email:
        flash("לא נמצאו פרטי משתמש מחובר. התחברי מחדש.", "error")
        return redirect(url_for("login"))

    if role == "employee":
        employee = get_employee_from_db(email)

        if not employee:
            flash("לא נמצאו פרטי עובד.", "error")
            return redirect(url_for("employee_schedule"))

        user = {
            "full_name": employee.get("name", ""),
            "email": employee.get("email", ""),
            "phone": "",
            "city": "",
            "about": "",
        }

        return render_template("profile.html", user=user)

    user = get_user_by_email(email)

    if not user:
        flash("לא נמצאו פרטי משתמש.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        city = request.form.get("city", "").strip()
        about = request.form.get("about", "").strip()

        update_user_profile(email, full_name, phone, city, about)

        session["user"] = full_name
        flash("הפרטים עודכנו בהצלחה.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


@app.route("/delete-account", methods=["POST"])
def delete_account():
    if not session.get("user"):
        return redirect(url_for("login"))

    delete_user_by_email(session.get("email"))
    session.clear()
    flash("החשבון נמחק בהצלחה.", "success")
    return redirect(url_for("home"))


@app.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    users = get_registered_users()
    workers = get_farm_workers()
    job_applications = get_all_job_applications()
    bookings = get_all_tour_bookings()
    peppers, _ = list_peppers()
    tours = list_admin_tours()
    try:
        payments = get_all_payments()
    except Exception as exc:
        print(f"Warning: failed to load payments: {exc}")
        payments = []

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    active_bookings = [
        booking for booking in bookings
        if booking.get("status") != "cancelled"
    ]

    tours_this_week = [
        booking for booking in active_bookings
        if booking.get("preferred_date")
        and start_of_week <= booking.get("preferred_date") <= end_of_week
    ]

    try:
        satisfaction_summary = get_combined_satisfaction_summary()
    except Exception as exc:
        print(f"Warning: failed to load satisfaction summary: {exc}")
        satisfaction_summary = {
            "average_rating": 0,
            "rating_count": 0
        }

    stats = {
    "tours_this_week": len(tours_this_week),
    "pending_bookings": len(active_bookings),
    "users_count": len(users),
    "workers_count": len(workers),
    "active_peppers": get_active_peppers_count(),
    "tours_this_month": len(active_bookings),
    "payments_count": len(payments),
    "payments_total": sum(float(payment.get("amount") or 0) for payment in payments),
    "satisfaction_average": satisfaction_summary["average_rating"],
    "satisfaction_count": satisfaction_summary["rating_count"],
    "pending_applications": len([
        application for application in job_applications
        if application.get("status") == "pending"
    ]),
}

    return render_template(
    "admin/admin_dashboard.html",
    stats=stats,
    users=users,
    workers=workers,
    bookings=bookings,
    peppers=peppers,
    tours=tours,
    payments=payments,
    job_applications=job_applications,
)

@app.route("/admin/job-applications/<int:application_id>/approve", methods=["POST"])
def approve_admin_job_application(application_id):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    application = get_job_application_by_id(application_id)

    if not application:
        flash("בקשת העבודה לא נמצאה.", "error")
        return redirect(url_for("admin_dashboard"))

    user = get_user_by_email(application["email"])
    

    if not user:
        flash("לא ניתן לאשר מועמד שאינו רשום כמשתמש במערכת.", "error")
        return redirect(url_for("admin_dashboard"))

    update_user_role(application["email"], "employee")
    approve_job_application(application_id)

    create_notification(
        user["id"],
        "בקשת העבודה אושרה",
        "מזל טוב! בקשת העבודה שלך אושרה וכעת יש לך הרשאות עובד במערכת."
    )


    flash("המועמד אושר והפך לעובד בהצלחה.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/job-applications/<int:application_id>/reject", methods=["POST"])
def reject_admin_job_application(application_id):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    application = get_job_application_by_id(application_id)

    if not application:
        flash("בקשת העבודה לא נמצאה.", "error")
        return redirect(url_for("admin_dashboard"))

    user = get_user_by_email(application["email"])

    reject_job_application(application_id)

    if user:
        create_notification(
            user["id"],
            "בקשת העבודה נדחתה",
            "בקשת העבודה שלך נבדקה אך לא אושרה בשלב זה."
        )

    flash("בקשת העבודה נדחתה.", "success")
    return redirect(url_for("admin_dashboard"))



def _prepare_weekly_schedule_employee_availability(employees, submissions_by_email=None, week_start_date=None):
    submissions_by_email = submissions_by_email or {}
    employees_availability = []

    for employee in employees:
        constraints = {}
        submission = submissions_by_email.get(employee.get("email", "").lower())
        if not submission and week_start_date is not None:
            try:
                submission = get_worker_constraints(employee["email"], week_start_date)
            except Exception as exc:
                print(f"Warning: failed to load worker constraints for {employee.get('email')}: {exc}")
                submission = None

        if submission:
            for day_key, _day_label in WORK_DAYS:
                constraints[day_key] = submission.get(day_key)

        employees_availability.append({
            "name": employee.get("name", ""),
            "email": employee.get("email", ""),
            "role": employee.get("role") or "employee",
            "job": "עובד/ת חווה",
            "constraints": constraints,
        })

    return employees_availability


def _load_weekly_schedule_employees():
    try:
        return load_employees_from_db()
    except Exception as exc:
        print(f"Warning: failed to load employees for weekly schedule: {exc}")
        return []


def _load_weekly_schedule_submissions(week_start_date):
    try:
        submissions = get_worker_constraint_submissions_for_week(week_start_date)
    except Exception as exc:
        print(f"Warning: failed to load worker constraint submissions: {exc}")
        submissions = []

    return {
        submission.get("employee_email", "").lower(): submission
        for submission in submissions
    }


@app.route("/admin/weekly-schedule")
def admin_weekly_schedule():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    today = date.today()
    week_offset = normalize_week_offset(request.args.get("week", 1))
    next_week_start = week_start_for_offset(week_offset, today)
    closed_day_keys = load_closed_day_keys(next_week_start)
    employees = _load_weekly_schedule_employees()
    submissions_by_email = _load_weekly_schedule_submissions(next_week_start)
    week_days = build_week_days(next_week_start, closed_day_keys)
    schedule_status = load_weekly_schedule_status(next_week_start)
    constraints_status = load_weekly_constraints_status(next_week_start)
    saved_schedule_assignments = load_saved_schedule_assignments(next_week_start)
    has_saved_schedule = bool(saved_schedule_assignments)
    constraints_updates_open = are_constraint_updates_open(next_week_start)
    active_published_schedule = load_active_published_schedule()
    active_constraints_week = load_active_constraints_week_context()
    active_published_week_start = active_published_schedule.get("week_start_date")
    active_constraints_week_start = (
        active_constraints_week.get("week_start_date")
        if active_constraints_week
        else None
    )

    return render_template(
        "admin/weekly_schedule.html",
        today=today,
        week_days=week_days,
        saved_schedule_table=build_saved_schedule_table(week_days, saved_schedule_assignments),
        has_saved_schedule=has_saved_schedule,
        schedule_status=schedule_status,
        constraints_status=constraints_status,
        schedule_status_label=(
            "פורסם לעובדים"
            if schedule_status == "published"
            else (
                "טיוטה שמורה"
                if has_saved_schedule
                else ("טיוטה / בעריכה" if schedule_status == "draft" else "טרם נשמר סידור")
            )
        ),
        week_offset=week_offset,
        week_options=build_week_options(week_offset, today),
        next_week_start=next_week_start,
        next_week_end=next_week_start + timedelta(days=WORK_WEEK_END_OFFSET_DAYS),
        employees_availability=_prepare_weekly_schedule_employee_availability(
            employees,
            submissions_by_email,
            next_week_start,
        ),
        submission_statuses=build_submission_status(employees, submissions_by_email),
        constraints_updates_open=constraints_updates_open,
        active_published_week_start=active_published_week_start,
        active_constraints_week_start=active_constraints_week_start,
        active_constraints_week_end=(
            active_constraints_week_start + timedelta(days=WORK_WEEK_END_OFFSET_DAYS)
            if active_constraints_week_start
            else None
        ),
        is_active_constraints_week=active_constraints_week_start == next_week_start,
    )


@app.route("/admin/weekly-schedule/reset-constraints", methods=["POST"])
def reset_weekly_schedule_constraints():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = normalize_week_offset(request.form.get("week", 1))
    week_start_date = week_start_for_offset(week_offset)
    delete_worker_constraints_for_week(week_start_date)
    flash("אילוצי העובדים לשבוע שנבחר אופסו בהצלחה.", "success")
    return redirect(url_for("admin_weekly_schedule", week=week_offset))


@app.route("/admin/weekly-schedule/closed-day", methods=["POST"])
def update_weekly_schedule_closed_day():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = normalize_week_offset(request.form.get("week", 1))
    week_start_date = week_start_for_offset(week_offset)
    day_name = request.form.get("day_name", "")
    day_date_text = request.form.get("day_date", "")
    is_closed = request.form.get("is_closed") == "1"

    try:
        day_date = datetime.strptime(day_date_text, "%Y-%m-%d").date()
        set_closed_day(week_start_date, day_date, day_name, is_closed)
        flash("סטטוס היום עודכן בהצלחה.", "success")
    except Exception as exc:
        flash(f"שגיאה בעדכון סטטוס היום: {exc}", "error")

    return redirect(url_for("admin_weekly_schedule", week=week_offset))


@app.route("/admin/weekly-schedule/submission-window", methods=["POST"])
def update_weekly_schedule_submission_window():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = normalize_week_offset(request.form.get("week", 1))
    week_start_date = week_start_for_offset(week_offset)
    is_open = request.form.get("is_open") == "1"
    if is_open:
        if load_weekly_schedule_status(week_start_date) == "published":
            flash("אי אפשר לפתוח הגשת אילוצים לשבוע שכבר פורסם לו סידור עבודה.", "error")
            return redirect(url_for("admin_weekly_schedule", week=week_offset))
        open_constraints_for_week(week_start_date)
        flash("עדכון האילוצים נפתח לשבוע הנבחר.", "success")
    else:
        set_constraints_status_for_week(week_start_date, CONSTRAINTS_STATUS_CLOSED)
        flash("עדכון האילוצים נסגר לשבוע הנבחר.", "success")
    return redirect(url_for("admin_weekly_schedule", week=week_offset))


@app.route("/admin/weekly-schedule/save", methods=["POST"])
def save_admin_weekly_schedule():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = normalize_week_offset(request.form.get("week", 1))
    week_start_date = week_start_for_offset(week_offset)
    assignments_payload = request.form.get("assignments_payload", "[]")

    try:
        result = save_weekly_schedule_draft_from_payload(
            week_start_date,
            assignments_payload,
            publish=True,
        )
        open_week = result.get("open_constraints_week") or {}
        open_week_start = open_week.get("week_start_date")
        flash(
            "סידור העבודה נשמר ופורסם לעובדים בהצלחה. "
            f"נשמרו {result['assignments_count']} שיבוצים. "
            f"הגשת אילוצים נפתחה לשבוע {open_week_start.strftime('%d/%m/%Y') if open_week_start else 'הבא'}.",
            "success",
        )
    except Exception as exc:
        flash(f"שגיאה בשמירת סידור העבודה: {exc}", "error")

    return redirect(url_for("admin_weekly_schedule", week=week_offset))


@app.route("/admin/weekly-schedule/publish", methods=["POST"])
def publish_admin_weekly_schedule():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = normalize_week_offset(request.form.get("week", 1))
    week_start_date = week_start_for_offset(week_offset)

    try:
        result = publish_weekly_schedule_for_employees(week_start_date)
        open_week = result.get("open_constraints_week") or {}
        open_week_start = open_week.get("week_start_date")
        flash(
            "סידור העבודה פורסם לעובדים. "
            f"הגשת אילוצים נפתחה לשבוע {open_week_start.strftime('%d/%m/%Y') if open_week_start else 'הבא'}.",
            "success",
        )
    except Exception as exc:
        flash(f"שגיאה בפרסום סידור העבודה: {exc}", "error")

    return redirect(url_for("admin_weekly_schedule", week=week_offset))


@app.route("/admin/weekly-schedule/reset", methods=["POST"])
def reset_admin_weekly_schedule():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = normalize_week_offset(request.form.get("week", 1))
    week_start_date = week_start_for_offset(week_offset)

    try:
        reset_weekly_schedule_draft(week_start_date)
        flash("הסידור אופס. שבוע הגשת האילוצים הפעיל לא השתנה.", "success")
    except Exception as exc:
        flash(f"שגיאה באיפוס סידור העבודה: {exc}", "error")

    return redirect(url_for("admin_weekly_schedule", week=week_offset))

@app.route("/admin/users/<int:user_id>/deactivate", methods=["POST"])
def deactivate_admin_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    deactivate_user_by_id(user_id)
    flash("המשתמש בוטל בהצלחה.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/users/<int:user_id>/activate", methods=["POST"])
def activate_admin_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    activate_user_by_id(user_id)
    flash("המשתמש הופעל בהצלחה.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/bookings/<int:booking_id>/cancel", methods=["POST"])
def cancel_admin_booking(booking_id):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    cancel_tour_booking_by_id(booking_id)
    flash("ההזמנה בוטלה בהצלחה.", "success")
    return redirect(url_for("admin_dashboard"))

# דף FORGOT PASSWORD


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None
    success = None
    form_data = {
        "full_name": "",
        "email": ""
    }

    if request.method == "POST":
        form_data["full_name"] = request.form.get("full_name", "").strip()
        form_data["email"] = request.form.get("email", "").strip()

        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        user = get_user_by_email(form_data["email"])

        if not user:
            error = "האימייל לא קיים במערכת."
        elif user["full_name"].strip().lower() != form_data["full_name"].strip().lower():
            error = "שם המשתמש והאימייל אינם תואמים."
        elif len(new_password) < 8:
            error = "הסיסמה חייבת להכיל לפחות 8 תווים."
        elif new_password != confirm_password:
            error = "הסיסמאות אינן תואמות."
        else:
            password_hash = generate_password_hash(new_password)
            update_user_password(form_data["email"], password_hash)
            success = "הסיסמה עודכנה בהצלחה. כעת אפשר להתחבר."

            return render_template(
                "forgot_password.html",
                error=None,
                success=success,
                form_data={"full_name": "", "email": ""}
            )

    return render_template(
        "forgot_password.html",
        error=error,
        success=success,
        form_data=form_data
    )


def _split_includes(includes):
    return [
        item.strip()
        for item in str(includes or "").replace("\r", "\n").split("\n")
        if item.strip()
    ]


def _duration_label(tour_package):
    if tour_package.get("duration_minutes"):
        return f"{tour_package['duration_minutes']} דקות"
    return tour_package.get("duration") or ""


def _prepare_tour_package(tour_package):
    if not tour_package:
        return None

    prepared = dict(tour_package)
    if not prepared.get("max_people") and prepared.get("max_participants"):
        prepared["max_people"] = prepared.get("max_participants")
    prepared["includes_list"] = _split_includes(prepared.get("includes"))
    prepared["duration_label"] = _duration_label(prepared)
    return prepared


def _default_tour_packages():
    return [
        _prepare_tour_package({
            "id": 1,
            "title": "סיור בסיסי",
            "price": 80,
            "duration_minutes": 90,
            "max_people": 20,
            "description": "סיור מודרך בחווה, הכרות עם זני הפלפלים העיקריים וסיפור החווה",
            "includes": "הדרכה מקצועית\nסיור בחממות\nטעימות פלפלים\nתמונות מזכרת",
        }),
        _prepare_tour_package({
            "id": 2,
            "title": "סיור משפחתי",
            "price": 120,
            "duration_minutes": 120,
            "max_people": 15,
            "description": "סיור מותאם למשפחות עם פעילויות לילדים וסדנת הכנת רטבים",
            "includes": "פעילויות לילדים\nסדנת הכנת רטבים\nטעימות והדגמות\nמתנות לילדים",
        }),
        _prepare_tour_package({
            "id": 3,
            "title": "חוויה פרימיום",
            "price": 200,
            "duration_minutes": 180,
            "max_people": 12,
            "description": "סיור מעמיק כולל סדנת קטיף, הכנת רטבים וארוחה חקלאית",
            "includes": "סדנת קטיף בחממות\nהכנת רטבים אישית\nארוחה חקלאית\nמוצרי החווה",
        }),
    ]


def _load_active_tour_or_redirect(tour_package_id):
    try:
        tour_package = get_active_tour(tour_package_id)
    except Exception as exc:
        print(f"Warning: failed to load tour package: {exc}")
        tour_package = None

    if not tour_package:
        for fallback_package in _default_tour_packages():
            if fallback_package["id"] == tour_package_id:
                return fallback_package

    return _prepare_tour_package(tour_package)


def get_available_tour_slots(selected_date):
    """Temporary availability until admin working hours and blocked dates exist."""
    if selected_date < date.today():
        return []
    return ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]


def _parse_booking_date(raw_date):
    try:
        parsed_date = datetime.strptime(raw_date or "", "%Y-%m-%d").date()
    except ValueError:
        return None
    return parsed_date


@app.route("/tours")
def tours():
    try:
        tour_packages = [_prepare_tour_package(package) for package in list_active_tours()]
    except Exception as exc:
        print(f"Warning: failed to load tour packages: {exc}")
        tour_packages = _default_tour_packages()

    if not tour_packages:
        tour_packages = _default_tour_packages()

    try:
        rating_summary = get_tour_rating_summary()
    except Exception as exc:
        print(f"Warning: failed to load tour rating summary: {exc}")
        rating_summary = {}

    try:
        latest_ratings = get_latest_tour_ratings(limit=6)
    except Exception as exc:
        print(f"Warning: failed to load latest tour ratings: {exc}")
        latest_ratings = []

    return render_template(
        "tours.html",
        tour_packages=tour_packages,
        rating_summary=rating_summary,
        latest_ratings=latest_ratings,
    )

@app.route("/tours/calendar/<int:tour_package_id>", methods=["GET", "POST"])
def tour_calendar(tour_package_id):
    tour_package = _load_active_tour_or_redirect(tour_package_id)
    if not tour_package:
        flash("הסיור שנבחר לא נמצא.", "error")
        return redirect(url_for("tours"))

    errors = {}
    selected_date = ""

    if request.method == "POST":
        selected_date = request.form.get("selected_date", "").strip()
        parsed_date = _parse_booking_date(selected_date)

        if not selected_date:
            errors["selected_date"] = "אנא בחר תאריך"
        elif parsed_date is None:
            errors["selected_date"] = "תאריך לא תקין"
        elif parsed_date < date.today():
            errors["selected_date"] = "לא ניתן לבחור תאריך שעבר"

        if not errors:
            session["tour_booking_draft"] = {
                "tour_package_id": tour_package_id,
                "selected_date": selected_date,
            }
            return redirect(url_for("tour_time", tour_package_id=tour_package_id))

    return render_template(
        "tour_calendar.html",
        tour_package=tour_package,
        selected_date=selected_date,
        today=date.today().isoformat(),
        errors=errors,
    )


@app.route("/tours/time/<int:tour_package_id>", methods=["GET", "POST"])
def tour_time(tour_package_id):
    tour_package = _load_active_tour_or_redirect(tour_package_id)
    if not tour_package:
        flash("הסיור שנבחר לא נמצא.", "error")
        return redirect(url_for("tours"))

    draft = session.get("tour_booking_draft") or {}
    if draft.get("tour_package_id") != tour_package_id or not draft.get("selected_date"):
        return redirect(url_for("tour_calendar", tour_package_id=tour_package_id))

    parsed_date = _parse_booking_date(draft.get("selected_date"))
    if parsed_date is None or parsed_date < date.today():
        session.pop("tour_booking_draft", None)
        return redirect(url_for("tour_calendar", tour_package_id=tour_package_id))

    slots = get_available_tour_slots(parsed_date)
    errors = {}
    selected_time = request.form.get("selected_time", "").strip() if request.method == "POST" else ""
    participants = request.form.get("participants", "").strip() if request.method == "POST" else ""

    if request.method == "POST":
        if not selected_time:
            errors["selected_time"] = "אנא בחר שעה"
        elif selected_time not in slots:
            errors["selected_time"] = "השעה שנבחרה אינה זמינה"

        try:
            participants_value = int(participants)
        except ValueError:
            participants_value = 0

        if participants_value <= 0:
            errors["participants"] = "אנא הזן מספר משתתפים תקין"
        elif participants_value > int(tour_package.get("max_people") or 0):
            errors["participants"] = f"מספר המשתתפים לא יכול להיות גדול מ-{tour_package['max_people']}"

        if not errors:
            draft.update({
                "tour_package_id": tour_package_id,
                "tour_title": tour_package.get("title"),
                "selected_date": draft.get("selected_date"),
                "selected_time": selected_time,
                "participants": participants_value,
                "price": int(tour_package.get("price") or 0),
                "total_price": int(tour_package.get("price") or 0) * participants_value,
            })
            session["tour_booking_draft"] = draft
            return redirect(url_for("tour_details"))

    return render_template(
        "tour_time.html",
        tour_package=tour_package,
        selected_date=draft.get("selected_date"),
        slots=slots,
        selected_time=selected_time,
        participants=participants,
        errors=errors,
    )


@app.route("/tours-booking", methods=["GET", "POST"])
def tours_booking():
    success = None
    error = None
    booking_draft = session.get("tour_booking_draft") or {}

    try:
        tour_packages = list_active_tours()
    except Exception as exc:
        print(f"Warning: failed to load tour packages: {exc}")
        tour_packages = []

    if request.method == "POST":

        if "user_id" not in session:
            return render_template(
                "login.html",
                error="עליך להתחבר לפני ביצוע הזמנה"
            )

        form_email = request.form.get("email", "").strip().lower()
        session_email = session.get("email", "").strip().lower()

        if form_email != session_email:
            error = "ניתן לבצע הזמנה רק עם האימייל של המשתמש המחובר."

        else:
            try:
                create_tour_booking(request.form)
                notify_employees_about_new_booking(request.form)

                session.pop("tour_booking_draft", None)

                success = "ההזמנה נשמרה בהצלחה!"

            except Exception as exc:
                print(f"Warning: failed to save tour booking: {exc}")
                error = "אירעה שגיאה בשמירת ההזמנה."

    return render_template(
        "tours_booking.html",
        success=success,
        error=error,
        booking_draft=booking_draft,
        tour_packages=tour_packages
    )

@app.route("/tours/details", methods=["GET", "POST"])
def tour_details():
    booking_draft = session.get("tour_booking_draft") or {}
    required_fields = ["tour_title", "selected_date", "selected_time", "participants", "total_price"]
    if any(not booking_draft.get(field) for field in required_fields):
        return redirect(url_for("tours"))

    error = None

    if request.method == "POST":
        if "user_id" not in session:
            return render_template(
                "login.html",
                error="עליך להתחבר לפני ביצוע הזמנה"
            )

        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        notes = request.form.get("notes", "").strip()
        session_email = session.get("email", "").strip().lower()

        if email != session_email:
            error = "ניתן לבצע הזמנה רק עם האימייל של המשתמש המחובר."
        elif not full_name:
            error = "אנא הזן שם מלא."
        elif not phone:
            error = "אנא הזן מספר טלפון."
        else:
            booking_draft.update({
                "full_name": full_name,
                "phone": phone,
                "email": email,
                "notes": notes,
            })
            session["tour_booking_draft"] = booking_draft
            return redirect(url_for("tour_payment"))

    return render_template("tour_details.html", booking_draft=booking_draft, error=error)


def notify_employees_about_new_booking(booking_data):
    tour_title = booking_data.get("tour_type") or booking_data.get("tour_title") or "סיור"
    full_name = booking_data.get("full_name") or "מבקר"
    preferred_date = booking_data.get("preferred_date") or booking_data.get("selected_date") or "-"
    preferred_time = booking_data.get("preferred_time") or booking_data.get("selected_time") or "-"

    create_notification_for_all_employees(
        "הזמנה חדשה",
        (
            f"התקבלה הזמנת סיור חדשה עבור {full_name}, "
            f"לסיור {tour_title}, "
            f"בתאריך {preferred_date} ."
        )
    )

def notify_admins_about_new_booking(booking_data):
    tour_title = booking_data.get("tour_type") or booking_data.get("tour_title") or "סיור"
    full_name = booking_data.get("full_name") or "מבקר"
    preferred_date = booking_data.get("preferred_date") or booking_data.get("selected_date") or "-"

    create_notification_for_all_admins(
        "הזמנת סיור חדשה",
        (
            f"התקבלה הזמנת סיור חדשה ששולמה עבור {full_name}, "
            f"לסיור {tour_title}, בתאריך {preferred_date}."
        )
    )

@app.route("/tours/payment", methods=["GET", "POST"])
def tour_payment():
    booking_draft = session.get("tour_booking_draft") or {}

    required_fields = [
        "tour_title",
        "selected_date",
        "selected_time",
        "participants",
        "total_price",
        "full_name",
        "phone",
        "email",
    ]

    if any(not booking_draft.get(field) for field in required_fields):
        return redirect(url_for("tour_details"))

    error = None
    success = None

    if request.method == "POST":
        booking_form = {
            "tour_type": booking_draft.get("tour_title"),
            "full_name": booking_draft.get("full_name"),
            "phone": booking_draft.get("phone"),
            "email": booking_draft.get("email"),
            "preferred_date": booking_draft.get("selected_date"),
            "preferred_time": booking_draft.get("selected_time"),
            "participants": booking_draft.get("participants"),
            "notes": booking_draft.get("notes", ""),
            "total_price": booking_draft.get("total_price"),
            "payment_status": "Paid",
        }

        try:
            booking_id = create_tour_booking(booking_form)

            create_payment({
                "booking_id": booking_id,
                "full_name": booking_draft.get("full_name"),
                "email": booking_draft.get("email"),
                "amount": booking_draft.get("total_price"),
                "payment_method": "Credit Card",
                "payment_status": "Paid",
            })

            notify_employees_about_new_booking(booking_form)
            notify_admins_about_new_booking(booking_form)

            session.pop("tour_booking_draft", None)
            success = "ההזמנה נשמרה בהצלחה!"

        except Exception as exc:
            print(f"Warning: failed to save tour booking/payment: {exc}")
            error = "אירעה שגיאה בשמירת ההזמנה."

    return render_template(
        "tour_payment.html",
        booking_draft=booking_draft,
        error=error,
        success=success,
    )

@app.route("/my-booked-tours")
def my_booked_tours():
    if not session.get("user"):
        flash("עליך להתחבר כדי לצפות בהזמנות שלך.", "warning")
        return redirect(url_for("login"))

    bookings = get_paid_tour_bookings_by_email(session.get("email"))

    today = date.today()

    for booking in bookings:
        booking["can_cancel"] = False

        try:
            tour_date = booking.get("preferred_date")

            if isinstance(tour_date, str):
                tour_date = datetime.strptime(tour_date, "%Y-%m-%d").date()

            days_left = (tour_date - today).days

            if days_left >= 2 and booking.get("status") != "Cancelled":
                booking["can_cancel"] = True

        except Exception:
            booking["can_cancel"] = False

    return render_template(
        "my_booked_tours.html",
        bookings=bookings
    )

@app.route("/post-tour-review", methods=["GET", "POST"])
def post_tour_review():
    if not session.get("user"):
        flash("עליך להתחבר כדי לדרג סיור.", "warning")
        return redirect(url_for("login"))

    email = session.get("email")
    pending_review = get_pending_tour_rating_for_user(email)

    if not pending_review:
        flash("אין לך כרגע סיור זמין לדירוג.", "info")
        return redirect(url_for("home"))

    if request.method == "POST":
        rating_raw = request.form.get("rating", "").strip()
        comment = request.form.get("comment", "").strip()

        try:
            rating = int(rating_raw)
        except ValueError:
            rating = 0

        if rating < 1 or rating > 5:
            flash("יש לבחור דירוג בין 1 ל־5 כוכבים.", "danger")
            return render_template("post_tour_review.html", booking=pending_review)

        success, message = create_tour_rating(
            email=email,
            booking_id=pending_review["booking_id"],
            rating=rating,
            comment=comment,
        )

        if success:
            flash(message, "success")
            return redirect(url_for("home"))

        flash(message, "danger")

    return render_template("post_tour_review.html", booking=pending_review)


@app.route("/my-booked-tours/cancel/<int:booking_id>", methods=["POST"])
def cancel_my_booked_tour(booking_id):
    if not session.get("user"):
        flash("עליך להתחבר כדי לבטל הזמנה.", "warning")
        return redirect(url_for("login"))

    success, message = cancel_user_tour_booking(
        booking_id=booking_id,
        email=session.get("email")
    )

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("my_booked_tours"))

@app.route("/admin/tours")
def admin_tours():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add-tour", methods=["GET", "POST"])
@app.route("/admin/tours/add", methods=["GET", "POST"])
def add_tour():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    errors = {}
    form_data = empty_tour_form_data()
    form_data["is_active"] = True

    if request.method == "POST":
        form_data = normalize_tour_form(request.form)

        image_path = save_tour_image(request.files.get("image_file"))
        if image_path:
            form_data["image_url"] = image_path
        else:
            form_data["image_url"] = request.form.get("existing_image_url", "").strip()

        tour_id, errors = create_tour_from_form(form_data)

        if not errors:
            flash("הסיור נוסף בהצלחה.", "success")
            return redirect(url_for("tours"))

        flash("יש לתקן את השדות המסומנים ולנסות שוב.", "error")

    return render_template(
        "admin/add_tour.html",
        errors=errors,
        form_data=form_data,
        form_title="הוספת סיור חדש",
        form_subtitle="ניהול סיורים במערכת חוות הפלפלים",
        submit_label="שמירת סיור",
        form_action=url_for("add_tour"),
        today_date=date.today().isoformat(),
    )

@app.route("/admin/tours/<int:package_id>/edit", methods=["GET", "POST"])
def edit_tour(package_id):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    errors = {}
    form_data = get_tour_edit_form(package_id)

    if not any(value for key, value in form_data.items() if key != "is_active"):
        flash("הסיור לא נמצא.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        form_data = normalize_tour_form(request.form)

        image_path = save_tour_image(request.files.get("image_file"))
        if image_path:
            form_data["image_url"] = image_path
        else:
            form_data["image_url"] = request.form.get("existing_image_url", "").strip()

        was_updated, errors = update_tour_from_form(package_id, form_data)

        if was_updated:
            flash("הסיור עודכן בהצלחה.", "success")
            return redirect(url_for("tours"))

        flash("יש לתקן את השדות המסומנים ולנסות שוב.", "error")

    return render_template(
        "admin/edit_tour.html",
        errors=errors,
        form_data=form_data,
        form_title="עריכת סיור",
        form_subtitle="עדכון פרטי הסיור, מחיר וזמינות",
        submit_label="עדכון סיור",
        form_action=url_for("edit_tour", package_id=package_id),
        today_date=date.today().isoformat(),
    )


@app.route("/admin/tours/<int:package_id>/delete", methods=["POST"])
def delete_tour(package_id):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    tour = get_active_tour(package_id)

    if not tour:
        flash("הסיור לא נמצא.", "error")
        return redirect(url_for("tours"))

    if has_active_paid_bookings_for_tour(tour["title"]):
        flash("לא ניתן למחוק סיור שכבר קיימות עבורו הזמנות ששולמו.", "error")
        return redirect(url_for("tours"))

    if delete_tour_from_service(package_id):
        flash("הסיור נמחק בהצלחה.", "success")
    else:
        flash("מחיקת הסיור נכשלה.", "error")

    return redirect(url_for("tours")) 

@app.route("/tour-booking-form", methods=["GET", "POST"])
def tour_booking_form():

    success = None
    error = None

    selected_tour = request.args.get("tour_type", "")

    booking_draft = session.get("tour_booking_draft") or {}

    if request.method == "POST":

        selected_tour = request.form.get("tour_type", "")

        if "user_id" not in session:
            return render_template(
                "login.html",
                error="עליך להתחבר לפני ביצוע הזמנה"
            )

        form_email = request.form.get("email", "").strip().lower()
        session_email = session.get("email", "").strip().lower()

        if form_email != session_email:

            error = "ניתן לבצע הזמנה רק עם האימייל של המשתמש המחובר."

            return render_template(
                "tour_booking_form.html",
                selected_tour=selected_tour,
                success=success,
                error=error,
                booking_draft=booking_draft
            )

        try:

            create_tour_booking(request.form)
            notify_employees_about_new_booking(request.form)


            session.pop("tour_booking_draft", None)

            success = "ההזמנה נשמרה בהצלחה!"

        except Exception as exc:

            print(f"Warning: failed to save tour booking: {exc}")

            error = "אירעה שגיאה בשמירת ההזמנה."

    return render_template(
        "tour_booking_form.html",
        selected_tour=selected_tour,
        success=success,
        error=error,
        booking_draft=booking_draft
    )
@app.route("/book-tour")
def book_tour():
    return render_template("book_tour.html")

@app.route("/pepper-varieties")
def pepper_varieties():
    selected_heat_levels = request.args.getlist("heat_level")
    peppers, selected_heat_levels = list_peppers(selected_heat_levels)
    heat_levels = list_heat_levels()

    return render_template(
        "pepper_varieties.html",
        peppers=peppers,
        heat_levels=heat_levels,
        selected_heat_levels=selected_heat_levels
    )


@app.route("/admin/add-pepper", methods=["GET", "POST"])
@app.route("/admin/peppers/add", methods=["GET", "POST"])
def add_pepper():
    if session.get("role") != "admin":
        flash("רק מנהל יכול להוסיף זן פלפל.", "error")
        return redirect(url_for("pepper_varieties"))

    errors = {}
    form_data = empty_pepper_form_data()

    if request.method == "POST":
        form_data = normalize_pepper_form(request.form)
        image_path = save_pepper_image(request.files.get("image_file"))
        if image_path:
            form_data["image_url"] = image_path
        else:
            form_data["image_url"] = request.form.get("existing_image_url", "").strip()
        pepper_id, errors = create_pepper_from_form(form_data)

        if not errors:
            flash("זן הפלפל נוסף בהצלחה.", "success")
            return redirect(url_for("pepper_varieties"))

        flash("יש לתקן את השדות המסומנים ולנסות שוב.", "error")

    return render_template(
        "add_pepper.html",
        errors=errors,
        form_data=form_data,
        heat_levels=list_heat_levels(),
        form_title="הוספת זן פלפל חדש",
        form_subtitle=(
            "ניהול זני פלפלים "
            "במערכת החווה"
        ),
        submit_label="שמירת פלפל",
        form_action=url_for("add_pepper"),
    )


@app.route("/admin/peppers/<int:pepper_id>/edit", methods=["GET", "POST"])
def edit_pepper(pepper_id):
    if session.get("role") != "admin":
        flash("רק מנהל יכול לערוך זן פלפל.", "error")
        return redirect(url_for("pepper_varieties"))

    errors = {}
    form_data = get_pepper_edit_form(pepper_id)
    if not any(form_data.values()):
        flash("זן הפלפל לא נמצא.", "error")
        return redirect(url_for("pepper_varieties"))

    if request.method == "POST":
        form_data = normalize_pepper_form(request.form)

        image_path = save_pepper_image(request.files.get("image_file"))
        if image_path:
            form_data["image_url"] = image_path
        else:
            form_data["image_url"] = request.form.get("existing_image_url", "").strip()

        was_updated, errors = update_pepper_from_form(pepper_id, form_data)

        if was_updated:
            flash("זן הפלפל עודכן בהצלחה.", "success")
            return redirect(url_for("pepper_varieties"))

        flash("יש לתקן את השדות המסומנים ולנסות שוב.", "error")

    return render_template(
        "add_pepper.html",
        errors=errors,
        form_data=form_data,
        heat_levels=list_heat_levels(),
        form_title="עריכת זן פלפל",
        form_subtitle=(
            "עדכון פרטי הזן "
            "ורמת החריפות"
        ),
        submit_label="עדכון פלפל",
        form_action=url_for("edit_pepper", pepper_id=pepper_id),
    )


@app.route("/admin/peppers/<int:pepper_id>/delete", methods=["POST"])
def delete_admin_pepper(pepper_id):
    if session.get("role") != "admin":
        flash("רק מנהל יכול למחוק זן פלפל.", "error")
        return redirect(url_for("pepper_varieties"))

    if delete_pepper(pepper_id):
        flash("זן הפלפל נמחק בהצלחה.", "success")
    else:
        flash("מחיקת זן הפלפל נכשלה.", "error")

    return redirect(url_for("pepper_varieties"))

@app.route("/farm-map")
def farm_map():
    if session.get("role") not in ["admin", "employee"]:
        return redirect(url_for("home"))
    return render_template("farm_map.html")

@app.route('/about')
def about():
    approved_workers = len([
    app for app in get_all_job_applications()
    if app.get('status') == 'approved'
]) + len(load_employees_from_db())
    return render_template('about.html', approved_workers=approved_workers)

@app.route('/job-application', methods=['GET', 'POST'])
@visitor_only
def job_application():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        worked_before = int(request.form.get('worked_before', 0))
        experience = request.form['experience']

        create_job_application(
            full_name,
            email,
            phone,
            worked_before,
            experience
        )

        flash('🌶️ הבקשה הוגשה בהצלחה! נחזור אליך בהקדם')
        create_notification_for_all_admins(
            "בקשת עבודה חדשה",
            f"הוגשה בקשת עבודה חדשה על ידי {full_name}, אימייל: {email}."
            )
        flash('הבקשה הוגשה בהצלחה! נחזור אליך בהקדם 🌶️')
        return redirect(url_for('job_application'))

    return render_template('job_application.html')

def load_attendance_data():
    return get_employee_attendance_from_db()


def save_attendance_data(data):
    return None


def get_employee_by_email(email):
    return get_employee_from_db(email)

def _parse_shift_time(time_text):
    try:
        return datetime.strptime(time_text, "%H:%M").time()
    except (TypeError, ValueError):
        return None


def _shift_hours(start_text, end_text):
    start_time = _parse_shift_time(start_text)
    end_time = _parse_shift_time(end_text)
    if not start_time or not end_time:
        return 0

    today = date.today()
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)
    if end_datetime <= start_datetime:
        return 0

    return round((end_datetime - start_datetime).seconds / 3600, 2)


def _worker_dashboard_data(employee):
    day_labels = {
        "Sunday": "ראשון",
        "Monday": "שני",
        "Tuesday": "שלישי",
        "Wednesday": "רביעי",
        "Thursday": "חמישי",
        "Friday": "שישי",
        "Saturday": "שבת",
    }
    day_offsets = {
        "Sunday": 0,
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
    }

    today = date.today()
    start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
    shifts = employee.get("shifts", []) if employee else []

    schedule_rows = []
    total_weekly_hours = 0

    for shift in shifts:
        day_name = shift.get("day", "")
        shift_date = start_of_week + timedelta(days=day_offsets.get(day_name, 0))
        hours = _shift_hours(shift.get("start"), shift.get("end"))
        total_weekly_hours += hours

        schedule_rows.append({
            "day": day_labels.get(day_name, day_name),
            "date": shift_date.strftime("%d/%m"),
            "start": shift.get("start", "-"),
            "end": shift.get("end", "-"),
            "shift_type": shift.get("status", "Scheduled"),
            "role": "עובד חווה",
            "note": f"הפסקה: {shift.get('break_time', '-')}",
            "badge_class": "shift-agriculture",
        })

    next_shift = "אין משמרת מתוכננת"
    for row in schedule_rows:
        if row["start"] != "-":
            next_shift = f"{row['day']}, {row['start']}"
            break

    return {
        "schedule_rows": schedule_rows,
        "next_shift": next_shift,
        "weekly_shift_count": len(schedule_rows),
        "weekly_hours": round(total_weekly_hours, 2),
        "monthly_hours": round(total_weekly_hours, 2),
    }

def _worker_dashboard_data_from_published_summary(schedule_summary, monthly_summary=None):
    shifts = schedule_summary.get("shifts", []) if schedule_summary else []
    next_shift = "אין משמרת מתוכננת"
    for shift in shifts:
        if shift.get("start"):
            next_shift = f"{shift.get('day', '-')}, {shift.get('start')}"
            break
    total_hours = schedule_summary.get("total_hours", 0) if schedule_summary else 0
    monthly_hours = (
        monthly_summary.get("total_hours", 0)
        if monthly_summary
        else total_hours
    )
    return {
        "schedule_rows": [],
        "next_shift": next_shift,
        "weekly_shift_count": schedule_summary.get("shift_count", 0) if schedule_summary else 0,
        "weekly_hours": round(total_hours, 2),
        "monthly_hours": round(monthly_hours, 2),
    }




@app.route("/worker-dashboard")
def worker_dashboard():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    try:
        active_schedule = load_active_published_schedule()
    except Exception as exc:
        print(f"Warning: failed to load active published weekly schedule: {exc}")
        active_schedule = {
            "week_start_date": None,
            "rows": [],
            "employee_summaries": {},
        }

    employee_email = session.get("email", "").lower()
    weekly_schedule_start = active_schedule.get("week_start_date") or week_start_for_offset(0)

    if not active_schedule.get("rows"):
        try:
            active_schedule["rows"] = load_published_weekly_schedule(weekly_schedule_start)
        except Exception as exc:
            print(f"Warning: failed to load published weekly schedule rows: {exc}")
            active_schedule["rows"] = []

    employee_schedule = active_schedule.get("employee_summaries", {}).get(
        employee_email,
        {"shifts": [], "shift_count": 0, "total_hours": 0},
    )
    if not employee_schedule.get("shifts"):
        try:
            employee_schedule = load_employee_published_schedule(employee_email, weekly_schedule_start)
        except Exception as exc:
            print(f"Warning: failed to load employee published schedule: {exc}")
            employee_schedule = {"shifts": [], "shift_count": 0, "total_hours": 0}

    monthly_reference_date = date.today()
    try:
        monthly_schedule = load_employee_monthly_published_schedule(
            employee_email,
            monthly_reference_date,
        )
    except Exception as exc:
        print(f"Warning: failed to load monthly employee schedule: {exc}")
        monthly_schedule = {"shifts": [], "shift_count": 0, "total_hours": 0}

    dashboard_data = _worker_dashboard_data_from_published_summary(
        employee_schedule,
        monthly_schedule,
    )
    weekly_schedule_end = weekly_schedule_start + timedelta(days=5) if weekly_schedule_start else None

    return render_template(
        "worker_dashboard.html",
        worker_name=session.get("user", ""),
        schedule_rows=dashboard_data["schedule_rows"],
        published_weekly_schedule_rows=active_schedule.get("rows", []),
        weekly_schedule_start=weekly_schedule_start,
        weekly_schedule_end=weekly_schedule_end,
        week_offset=None,
        next_shift=dashboard_data["next_shift"],
        weekly_shift_count=dashboard_data["weekly_shift_count"],
        weekly_hours=dashboard_data["weekly_hours"],
        monthly_hours=dashboard_data["monthly_hours"],
    )

@app.route("/worker-constraints", methods=["GET", "POST"])
def worker_constraints():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    employee_email = session.get("email", "")
    error = None
    success_message = None
    option_labels = {**dict(AVAILABILITY_OPTIONS), **LEGACY_AVAILABILITY_LABELS}

    if request.method == "POST":
        is_update = request.form.get("is_editing") == "1"
        submission, week_start_date, error, was_saved = submit_worker_constraints(
            employee_email,
            request.form,
        )
        closed_days = get_closed_constraint_days(week_start_date) if week_start_date else set()
        constraints_updates_open = _worker_constraints_updates_open_for_route(week_start_date)
        if error in {CONSTRAINT_UPDATES_CLOSED_MESSAGE, CONSTRAINT_SUBMISSION_CLOSED_MESSAGE}:
            constraints_updates_open = False

        if was_saved:
            return redirect(url_for(
                "worker_constraints",
                submitted="1",
                updated="1" if is_update else "0",
            ))

        return render_template(
            "worker_constraints.html",
            worker_name=session.get("user", ""),
            days=WORK_DAYS,
            options=AVAILABILITY_OPTIONS,
            options_by_day=get_availability_options_by_day(),
            option_labels=option_labels,
            form_data=request.form,
            submission=submission,
            is_editing=constraints_updates_open,
            constraints_updates_open=constraints_updates_open,
            week_start_date=week_start_date,
            week_end_date=week_start_date + timedelta(days=5) if week_start_date else None,
            closed_days=closed_days,
            closed_day_message=CLOSED_DAY_MESSAGE,
            error=error,
            success_message=None,
        )

    submission, week_start_date = get_existing_constraints(employee_email)
    constraints_updates_open = _worker_constraints_updates_open_for_route(week_start_date)
    is_editing = constraints_updates_open and request.args.get("edit") == "1"
    closed_days = get_closed_constraint_days(week_start_date) if week_start_date else set()

    if week_start_date is None:
        success_message = NO_ACTIVE_CONSTRAINT_WEEK_MESSAGE
    elif not constraints_updates_open:
        success_message = CONSTRAINT_UPDATES_CLOSED_MESSAGE if submission else CONSTRAINT_SUBMISSION_CLOSED_MESSAGE
    elif submission:
        if request.args.get("updated") == "1":
            success_message = "האילוצים עודכנו בהצלחה ונשלחו למנהל."
        elif request.args.get("submitted") == "1":
            success_message = "האילוצים נשמרו בהצלחה ונשלחו למנהל."
        else:
            success_message = "האילוצים שלך לשבוע הבא כבר נשמרו. ניתן לערוך ולעדכן אותם בכל זמן."

    return render_template(
        "worker_constraints.html",
        worker_name=session.get("user", ""),
        days=WORK_DAYS,
        options=AVAILABILITY_OPTIONS,
        options_by_day=get_availability_options_by_day(),
        option_labels=option_labels,
        form_data={},
        submission=submission,
        is_editing=is_editing,
        constraints_updates_open=constraints_updates_open,
        week_start_date=week_start_date,
        week_end_date=week_start_date + timedelta(days=5) if week_start_date else None,
        closed_days=closed_days,
        closed_day_message=CLOSED_DAY_MESSAGE,
        error=error,
        success_message=success_message,
    )


@app.route("/worker-tours")
def worker_tours():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    worker_id = session.get("user_id")

    if isinstance(worker_id, str) and worker_id.isdigit():
        worker_id = int(worker_id)

    if not isinstance(worker_id, int):
        return render_template(
        "worker_tours.html",
        worker_name=session.get("user", ""),
        bookings=[],
    )

    

    bookings = []

    try:
        conn = get_connection()
        cursor = conn.cursor()
    except ValueError:
        return render_template(
            "worker_tours.html",
            worker_name=session.get("user", ""),
            bookings=[
    {
        "preferred_date": "2026-01-01",
        "preferred_time": "08:00",
        "full_name": "Test Visitor",
        "tour_type": "Test Tour",
        "participants": 1,
        "email": "test@example.com",
        "status": "confirmed"
    },
    {
        "preferred_date": "2026-01-01",
        "preferred_time": "18:00",
        "full_name": "Test Visitor",
        "tour_type": "Test Tour",
        "participants": 1,
        "email": "test@example.com",
        "status": "confirmed"
    }
]

        )

    cursor.execute("""
        SELECT
            preferred_date,
            preferred_time,
            full_name,
            tour_type,
            participants,
            email,
            status
        FROM dbo.tour_bookings
        WHERE assigned_worker_id = ?
        ORDER BY preferred_date, preferred_time
    """, (worker_id,))

    rows = cursor.fetchall()

    bookings = []
    for row in rows:
        bookings.append({
            "preferred_date": row[0],
            "preferred_time": row[1],
            "full_name": row[2],
            "tour_type": row[3],
            "participants": row[4],
            "email": row[5],
            "status": row[6],
        })

    cursor.close()
    conn.close()

    return render_template(
        "worker_tours.html",
        worker_name=session.get("user", ""),
        bookings=bookings
    )

@app.route("/employee-schedule")
def employee_schedule():
    if session.get("role") != "employee" and session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = int(request.args.get("week", 0))
    week_start_date = week_start_for_offset(week_offset)
    week_end_date = week_start_date + timedelta(days=5)

    empty_schedule = {"shifts": [], "shift_count": 0, "total_hours": 0}

    def attach_published_schedule(employee):
        if not employee:
            return None

        try:
            schedule_summary = load_employee_published_schedule(
                employee.get("email", ""),
                week_start_date,
            )
        except Exception as exc:
            print(f"Warning: failed to load employee published schedule: {exc}")
            schedule_summary = empty_schedule

        employee_copy = dict(employee)
        employee_copy["published_schedule"] = schedule_summary or empty_schedule
        return employee_copy

    if session.get("role") == "admin" and session.get("view_employee_email"):
        employee = get_employee_by_email(session.get("view_employee_email"))
        employees = [attach_published_schedule(employee)] if employee else []

    elif session.get("role") == "employee":
        employee = get_employee_by_email(session.get("email"))
        employees = [attach_published_schedule(employee)] if employee else []

    else:
        employees = [
            attach_published_schedule(employee)
            for employee in load_employees_from_db()
        ]

    return render_template(
        "employee_schedule.html",
        employees=[employee for employee in employees if employee],
        week_start_date=week_start_date,
        week_end_date=week_end_date,
        week_offset=week_offset,
    )

@app.route("/weekly-shift-calendar")
def weekly_shift_calendar():
    if session.get("role") != "employee" and session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = int(request.args.get("week", 0))

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6)

    week_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    if session.get("role") == "employee":
        employee = get_employee_by_email(session.get("email"))
        employees = [employee] if employee else []

    elif session.get("role") == "admin" and session.get("view_employee_email"):
        employee = get_employee_by_email(session.get("view_employee_email"))
        employees = [employee] if employee else []

    else:
        employees = load_employees_from_db()

    attendance_data = load_attendance_data()

    weekly_history = []
    weekly_hours = 0
    weekly_salary = 0
    monthly_salary = 0

    current_month = today.month
    current_year = today.year

    for employee in employees:
        email = employee["email"].lower()
        saved = attendance_data.get(email, {})

        if saved:
            employee["attendance"] = saved
            employee["status"] = "במשמרת" if saved.get("is_on_duty") else "לא במשמרת"

        history = saved.get("history", [])

        for item in history:
            item_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
            if item_date.month == current_month and item_date.year == current_year:
                monthly_salary += item.get("daily_salary", 0)

            if start_of_week <= item_date <= end_of_week:
                item_copy = dict(item)
                item_copy["employee_name"] = employee["name"]
                weekly_history.append(item_copy)
                weekly_hours += item.get("worked_hours", 0)
                weekly_salary += item.get("daily_salary", 0)

        if saved.get("is_on_duty"):
            weekly_history.append({
                "employee_name": employee["name"],
                "date": date.today().strftime("%Y-%m-%d"),
                "start_shift": saved.get("start_shift"),
                "end_shift": "עדיין במשמרת",
                "worked_hours": 0,
                "daily_salary": 0
            })

    return render_template(
        "weekly_shift_calendar.html",
        employees=employees,
        week_days=week_days,
        weekly_history=weekly_history,
        weekly_hours=round(weekly_hours, 2),
        weekly_salary=round(weekly_salary, 2),
        monthly_salary=round(monthly_salary, 2),
        week_offset=week_offset,
        start_of_week=start_of_week.strftime("%d/%m/%Y"),
        end_of_week=end_of_week.strftime("%d/%m/%Y")
    )


@app.route("/shift-status")
def shift_status():
    if session.get("role") != "employee" and session.get("role") != "admin":
        return redirect(url_for("home"))

    week_offset = int(request.args.get("week", 0))

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6)

    if session.get("role") == "admin" and session.get("view_employee_email"):
        employee = get_employee_by_email(session.get("view_employee_email"))
        employees = [employee] if employee else []

    elif session.get("role") == "employee":
        employee = get_employee_by_email(session.get("email"))
        employees = [employee] if employee else []

    else:
        employees = load_employees_from_db()

    attendance_data = load_attendance_data()

    weekly_history = []
    weekly_hours = 0
    weekly_salary = 0

    for employee in employees:
        email = employee["email"].lower()
        saved = attendance_data.get(email, {})

        if saved:
            employee["attendance"] = saved
            employee["status"] = "במשמרת" if saved.get("is_on_duty") else "לא במשמרת"

            for item in saved.get("history", []):
                item_date = datetime.strptime(item["date"], "%Y-%m-%d").date()

                if start_of_week <= item_date <= end_of_week:
                    weekly_history.append(item)
                    weekly_hours += item.get("worked_hours", 0)
                    weekly_salary += item.get("daily_salary", 0)

    stats = {
        "employees": len(employees),
        "total_shifts": sum(len(employee["shifts"]) for employee in employees),
        "total_hours": round(weekly_hours, 2),
        "total_salary": round(weekly_salary, 2)
    }

    return render_template(
        "shift_status.html",
        employees=employees,
        stats=stats,
        weekly_history=weekly_history,
        week_offset=week_offset,
        start_of_week=start_of_week.strftime("%d/%m/%Y"),
        end_of_week=end_of_week.strftime("%d/%m/%Y")
    )

@app.route("/start-shift", methods=["POST"])
def start_shift():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    email = session.get("email", "").lower()
    employee = get_employee_by_email(email)

    if employee:
        start_text = datetime.now().strftime("%H:%M")
        start_employee_shift_in_db(email, start_text)

    return redirect(url_for("shift_status"))


@app.route("/end-shift", methods=["POST"])
def end_shift():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    email = session.get("email", "").lower()
    employee = get_employee_by_email(email)

    if employee:
        attendance_data = load_attendance_data()
        attendance = attendance_data.get(email, {})

        start_text = attendance.get("start_shift")
        end_time = datetime.now()
        end_text = end_time.strftime("%H:%M")

        worked_hours = 0
        daily_salary = 0

        if start_text:
            start_hour, start_minute = map(int, start_text.split(":"))
            start_time = end_time.replace(
                hour=start_hour,
                minute=start_minute,
                second=0,
                microsecond=0
            )

            worked_hours = round((end_time - start_time).seconds / 3600, 2)
            daily_salary = round(worked_hours * employee["hourly_rate"], 2)

        end_employee_shift_in_db(email, end_text, worked_hours, daily_salary)

    return redirect(url_for("shift_status"))

@app.route("/work-planning")
def work_planning():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    return render_template(
    "work_planning.html",
    employees=load_employees_from_db()
)



@app.route("/work-planning/employee/<email>")
def work_planning_employee(email):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    employee = get_employee_by_email(email)

    if not employee:
        return redirect(url_for("work_planning"))

    return render_template("work_planning_employee.html", employee=employee)

@app.route("/work-planning/employee/<email>/update", methods=["POST"])
def update_employee_schedule(email):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    employee = get_employee_by_email(email)

    if not employee:
        return redirect(url_for("work_planning"))

    hourly_rate = float(request.form.get("hourly_rate", employee["hourly_rate"]))
    shift_count = int(request.form.get("shift_count", 0))

    updated_shifts = []

    for index in range(shift_count):
        updated_shifts.append({
            "day": request.form.get(f"day_{index}"),
            "start": request.form.get(f"start_{index}"),
            "end": request.form.get(f"end_{index}"),
            "break_time": request.form.get(f"break_{index}"),
            "status": "Scheduled",
        })

    update_employee_schedule_in_db(email, hourly_rate, updated_shifts)

    return redirect(url_for("work_planning_employee", email=email))

@app.route("/admin/view-as-employee/<email>")
def view_as_employee(email):
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    employee = get_employee_by_email(email)

    if not employee:
        return redirect(url_for("work_planning"))

    session["view_employee_email"] = employee["email"]
    return redirect(url_for("employee_schedule"))

@app.route("/admin/view-all-employees")
def view_all_employees():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    session.pop("view_employee_email", None)
    return redirect(url_for("weekly_shift_calendar"))

@app.route("/check-session")
def check_session():
    return str(dict(session))

@app.route("/website-feedback", methods=["GET", "POST"])
def website_feedback():
    if not session.get("user"):
        flash("עליך להתחבר כדי לשלוח משוב על האתר.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        rating_raw = request.form.get("rating", "").strip()
        comment = request.form.get("comment", "").strip()

        try:
            rating = int(rating_raw)
        except ValueError:
            rating = 0

        if rating < 1 or rating > 5:
            flash("יש לבחור דירוג בין 1 ל־5 כוכבים.", "danger")
            return render_template("website_feedback.html")

        success, message = create_website_feedback(
            email=session.get("email"),
            full_name=session.get("user"),
            rating=rating,
            comment=comment,
        )

        if success:
            flash(message, "success")
            return redirect(url_for("home"))

        flash(message, "danger")

    return render_template("website_feedback.html")

@app.route("/notifications")
def notifications():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") not in ["employee", "admin"]:
        return redirect(url_for("home"))

    user_notifications = get_user_notifications(session["user_id"])

    return render_template(
        "notifications.html",
        notifications=user_notifications
    )


@app.route("/notifications/<int:notification_id>/read", methods=["POST"])
def read_notification(notification_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") not in ["employee", "admin"]:
        return redirect(url_for("home"))

    mark_notification_as_read(notification_id, session["user_id"])

    return redirect(url_for("notifications"))


@app.context_processor
def inject_notifications_count():
    if "user_id" not in session or session.get("role") not in ["employee", "admin"]:
        return {
            "unread_notifications_count": 0,
            "header_notifications": []
        }

    try:
        count = get_unread_notifications_count(session["user_id"])
        notifications = get_user_notifications(session["user_id"])[:5]
    except Exception:
        count = 0
        notifications = []

    return {
        "unread_notifications_count": count,
        "header_notifications": notifications
    }


if __name__ == "__main__":
    initialize_database()

    if os.getenv("INIT_ADMIN_ON_STARTUP", "").lower() in {"1", "true", "yes"}:
        initialize_admin()
    else:
        print("Admin initialization skipped on startup. Set INIT_ADMIN_ON_STARTUP=true to enable it.")

    app.run(debug=os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"})


