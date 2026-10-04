import os

from werkzeug.security import generate_password_hash

from backend.data_access.user_repository import (
    create_user,
    get_user_by_email,
    update_user_password,
    update_user_role,
)
from backend.domain.user import User


# if the INIT_ADMIN_ON_STARTUP in the env file is true return true otherwise return false
def _is_enabled(value):
    return (value or "").lower() in {"1", "true", "yes"}


# Ensure an admin user exists
def ensure_admin_user():
    if not _is_enabled(os.getenv("INIT_ADMIN_ON_STARTUP")):
        return False

    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    full_name = os.getenv("ADMIN_FULL_NAME", "System Admin").strip() or "System Admin"

    if not email:
        raise ValueError("ADMIN_EMAIL is required when INIT_ADMIN_ON_STARTUP=true")

    if not password:
        raise ValueError("ADMIN_PASSWORD is required when INIT_ADMIN_ON_STARTUP=true")

    password_hash = generate_password_hash(password)
    existing_user = get_user_by_email(email)

    if existing_user:
        update_user_role(email, "admin")
        update_user_password(email, password_hash)
        # cant make more than one admin
        return False

    # if there is no admin user create one
    admin_user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role="admin",
    )

    create_user(admin_user)
    return True
