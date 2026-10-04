from backend.data_access.db import fetchall_dicts, fetchone_dict, get_connection

TOURS_TABLE = "dbo.tour_packages"


def _log_db_error(operation, exc):
    print(f"Warning: tour database operation failed during {operation}: {exc}")


def _duration_label(duration_minutes):
    return f"{duration_minutes} דקות"


def get_active_tours():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT *
            FROM {TOURS_TABLE}
            WHERE is_active = 1
            ORDER BY price ASC, id ASC
        """)
        return fetchall_dicts(cursor)
    except Exception as exc:
        _log_db_error("get_active_tours", exc)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_all_tours():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT *
            FROM {TOURS_TABLE}
            ORDER BY created_at DESC, id DESC
        """)
        return fetchall_dicts(cursor)
    except Exception as exc:
        _log_db_error("get_all_tours", exc)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_active_tour_by_id(tour_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT *
            FROM {TOURS_TABLE}
            WHERE id = ? AND is_active = 1
        """, (tour_id,))
        return fetchone_dict(cursor)
    except Exception as exc:
        _log_db_error("get_active_tour_by_id", exc)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_tour_by_id(tour_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT *
            FROM {TOURS_TABLE}
            WHERE id = ?
        """, (tour_id,))
        return fetchone_dict(cursor)
    except Exception as exc:
        _log_db_error("get_tour_by_id", exc)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def create_tour(tour):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {TOURS_TABLE} (
                title,
                price,
                duration,
                duration_minutes,
                max_people,
                description,
                includes,
                image_url,
                available_from,
                available_until,
                is_active
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tour.title,
            tour.price,
            _duration_label(tour.duration_minutes),
            tour.duration_minutes,
            tour.max_people,
            tour.description,
            tour.includes,
            tour.image_url,
            tour.available_from,
            tour.available_until,
            1 if tour.is_active else 0,
        ))
        tour_id = cursor.fetchone()[0]
        conn.commit()
        return tour_id
    except Exception as exc:
        _log_db_error("create_tour", exc)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_tour(tour):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {TOURS_TABLE}
            SET title = ?,
                price = ?,
                duration = ?,
                duration_minutes = ?,
                max_people = ?,
                description = ?,
                includes = ?,
                image_url = ?,
                available_from = ?,
                available_until = ?,
                is_active = ?
            WHERE id = ?
        """, (
            tour.title,
            tour.price,
            _duration_label(tour.duration_minutes),
            tour.duration_minutes,
            tour.max_people,
            tour.description,
            tour.includes,
            tour.image_url,
            tour.available_from,
            tour.available_until,
            1 if tour.is_active else 0,
            tour.id,
        ))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as exc:
        _log_db_error("update_tour", exc)
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_tour_by_id(tour_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {TOURS_TABLE} WHERE id = ?", (tour_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as exc:
        _log_db_error("delete_tour_by_id", exc)
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
