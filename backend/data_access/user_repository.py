from backend.data_access.role_repository import get_role_id_by_name
from backend.data_access.db import fetchone_dict, fetchall_dicts, get_connection

USERS_TABLE = "dbo.users"
ROLES_TABLE = "dbo.roles"


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        SELECT
            users.id,
            users.full_name,
            users.email,
            users.password_hash,
            users.role_id,
            users.phone,
            users.city,
            users.about,
            roles.name AS role
        FROM {USERS_TABLE} AS users
        INNER JOIN {ROLES_TABLE} AS roles
            ON users.role_id = roles.id
        WHERE users.email = ?
    """
    cursor.execute(query, (email,))
    user = fetchone_dict(cursor)

    cursor.close()
    conn.close()

    return user


def create_user(user):
    role_id = user.role_id or get_role_id_by_name(user.role)
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        INSERT INTO {USERS_TABLE} (full_name, email, password_hash, role_id)
        VALUES (?, ?, ?, ?)
    """
    cursor.execute(query, (user.full_name, user.email, user.password_hash, role_id))

    conn.commit()
    cursor.close()
    conn.close()


def update_user_password(email, password_hash):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"UPDATE {USERS_TABLE} SET password_hash = ? WHERE email = ?"
    cursor.execute(query, (password_hash, email))

    conn.commit()
    cursor.close()
    conn.close()


def update_user_role(email, role):
    role_id = get_role_id_by_name(role)
    conn = get_connection()
    cursor = conn.cursor()

    query = f"UPDATE {USERS_TABLE} SET role_id = ? WHERE email = ?"
    cursor.execute(query, (role_id, email))

    conn.commit()
    cursor.close()
    conn.close()


def update_user_profile(email, full_name, phone, city, about):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        UPDATE {USERS_TABLE}
        SET full_name = ?, phone = ?, city = ?, about = ?
        WHERE email = ?
    """
    cursor.execute(query, (full_name, phone, city, about, email))

    conn.commit()
    cursor.close()
    conn.close()


def delete_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"DELETE FROM {USERS_TABLE} WHERE email = ?"
    cursor.execute(query, (email,))

    conn.commit()
    cursor.close()
    conn.close()


def get_users_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {USERS_TABLE}")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count


def get_registered_users():
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        SELECT
            users.id,
            users.full_name,
            users.email,
            users.phone,
            users.city,
            users.about,
            users.is_active,
            users.created_at,
            roles.name AS role
        FROM {USERS_TABLE} AS users
        INNER JOIN {ROLES_TABLE} AS roles
            ON users.role_id = roles.id
        WHERE roles.name = 'visitor'
        ORDER BY users.created_at DESC
    """

    cursor.execute(query)
    users = fetchall_dicts(cursor)

    cursor.close()
    conn.close()

    return users


def get_farm_workers():
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        SELECT
            users.id,
            users.full_name,
            users.email,
            users.phone,
            users.city,
            users.about,
            users.is_active,
            users.created_at,
            roles.name AS role
        FROM {USERS_TABLE} AS users
        INNER JOIN {ROLES_TABLE} AS roles
            ON users.role_id = roles.id
        WHERE roles.name = 'employee'
        ORDER BY users.created_at DESC
    """

    cursor.execute(query)
    workers = fetchall_dicts(cursor)

    cursor.close()
    conn.close()

    return workers


def deactivate_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        UPDATE {USERS_TABLE}
        SET is_active = 0
        WHERE id = ?
    """

    cursor.execute(query, (user_id,))

    conn.commit()
    cursor.close()
    conn.close()  

def activate_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        UPDATE {USERS_TABLE}
        SET is_active = 1
        WHERE id = ?
    """

    cursor.execute(query, (user_id,))

    conn.commit()
    cursor.close()
    conn.close()
