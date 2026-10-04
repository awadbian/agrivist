from backend.data_access.db import fetchone_dict, get_connection

ROLES_TABLE = "dbo.roles"


def get_role_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"SELECT id, name FROM {ROLES_TABLE} WHERE name = ?"
    cursor.execute(query, (name,))
    role = fetchone_dict(cursor)

    cursor.close()
    conn.close()

    return role


def get_role_id_by_name(name):
    role = get_role_by_name(name)
    if not role:
        raise ValueError(f"Role does not exist: {name}")

    return role["id"]
