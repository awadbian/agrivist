from backend.data_access.db import fetchall_dicts, fetchone_dict, get_connection

HEAT_LEVELS_TABLE = "dbo.pepper_heat_levels"


def _log_db_error(operation, exc):
    print(f"Warning: heat level database operation failed during {operation}: {exc}")


def get_all_heat_levels():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, level_value, name, min_scoville, max_scoville, color, css_class, description
            FROM {HEAT_LEVELS_TABLE}
            ORDER BY level_value ASC, min_scoville ASC
        """)
        return fetchall_dicts(cursor)
    except Exception as exc:
        _log_db_error("get_all_heat_levels", exc)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_heat_level_by_scoville(scoville_level):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT TOP 1 id, level_value, name, min_scoville, max_scoville, color, css_class, description
            FROM {HEAT_LEVELS_TABLE}
            WHERE ? BETWEEN min_scoville AND max_scoville
            ORDER BY level_value ASC, min_scoville ASC
        """, (scoville_level,))
        return fetchone_dict(cursor)
    except Exception as exc:
        _log_db_error("get_heat_level_by_scoville", exc)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_heat_level_by_value(level_value):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT TOP 1 id, level_value, name, min_scoville, max_scoville, color, css_class, description
            FROM {HEAT_LEVELS_TABLE}
            WHERE level_value = ?
            ORDER BY level_value ASC
        """, (level_value,))
        return fetchone_dict(cursor)
    except Exception as exc:
        _log_db_error("get_heat_level_by_value", exc)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
