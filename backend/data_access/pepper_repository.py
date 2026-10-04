from backend.data_access.db import fetchall_dicts, fetchone_dict, get_connection

PEPPERS_TABLE = "dbo.peppers"


def _log_db_error(operation, exc):
    print(f"Warning: pepper database operation failed during {operation}: {exc}")


# create the table of the pepper
def create_pepper(pepper):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO dbo.peppers (
                name,
                scientific_name,
                origin_country,
                color,
                scoville_level,
                heat_level_id,
                heat_category,
                description,
                culinary_tips,
                growing_tips,
                warnings,
                image_url,
                status,
                spray_info,
                watering_needs,
                sunlight_needs,
                season,
                use_cases,
                soil_type,
                temperature_range,
                irrigation_frequency,
                water_amount,
                harvest_season,
                days_to_harvest,
                harvest_signs,
                storage_tips,
                extra_info
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(query, (
            pepper.name,
            pepper.scientific_name,
            pepper.origin_country,
            pepper.color,
            pepper.scoville_level,
            pepper.heat_level_id,
            pepper.heat_category,
            pepper.description,
            pepper.culinary_tips,
            pepper.growing_tips,
            pepper.warnings,
            pepper.image_url,
            pepper.status,
            pepper.spray_info,
            pepper.watering_needs,
            pepper.sunlight_needs,
            pepper.season,
            pepper.use_cases,
            pepper.soil_type,
            pepper.temperature_range,
            pepper.irrigation_frequency,
            pepper.water_amount,
            pepper.harvest_season,
            pepper.days_to_harvest,
            pepper.harvest_signs,
            pepper.storage_tips,
            pepper.extra_info,
        ))

        pepper_id = cursor.fetchone()[0]
        conn.commit()
        return pepper_id
    except Exception as exc:
        _log_db_error("create_pepper", exc)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# to the page of the users
def get_all_peppers():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT
                peppers.*,
                heat_levels.name AS heat_level_name,
                heat_levels.level_value AS heat_level_value,
                heat_levels.color AS heat_level_color,
                heat_levels.css_class AS heat_level_css_class,
                heat_levels.description AS heat_level_description
            FROM {PEPPERS_TABLE} AS peppers
            LEFT JOIN dbo.pepper_heat_levels AS heat_levels
                ON heat_levels.id = peppers.heat_level_id
            ORDER BY peppers.id ASC
        """)
        return fetchall_dicts(cursor)
    except Exception as exc:
        _log_db_error("get_all_peppers", exc)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_peppers_by_scoville_level(scoville_level):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM dbo.peppers
            WHERE scoville_level = ?
            ORDER BY id ASC
        """
        cursor.execute(query, (scoville_level,))
        return fetchall_dicts(cursor)
    except Exception as exc:
        _log_db_error("get_peppers_by_scoville_level", exc)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_peppers_by_heat_level_id(heat_level_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                peppers.*,
                heat_levels.name AS heat_level_name,
                heat_levels.level_value AS heat_level_value,
                heat_levels.color AS heat_level_color,
                heat_levels.css_class AS heat_level_css_class,
                heat_levels.description AS heat_level_description
            FROM dbo.peppers AS peppers
            INNER JOIN dbo.pepper_heat_levels AS heat_levels
                ON heat_levels.id = peppers.heat_level_id
            WHERE peppers.heat_level_id = ?
            ORDER BY peppers.id ASC
        """
        cursor.execute(query, (heat_level_id,))
        return fetchall_dicts(cursor)
    except Exception as exc:
        _log_db_error("get_peppers_by_heat_level_id", exc)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_peppers_by_heat_level_values(heat_level_values):
    if not heat_level_values:
        return get_all_peppers()

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        placeholders = ", ".join("?" for _ in heat_level_values)

        query = f"""
            SELECT
                peppers.*,
                heat_levels.name AS heat_level_name,
                heat_levels.level_value AS heat_level_value,
                heat_levels.color AS heat_level_color,
                heat_levels.css_class AS heat_level_css_class,
                heat_levels.description AS heat_level_description
            FROM dbo.peppers AS peppers
            INNER JOIN dbo.pepper_heat_levels AS heat_levels
                ON heat_levels.id = peppers.heat_level_id
            WHERE heat_levels.level_value IN ({placeholders})
            ORDER BY peppers.id ASC
        """
        cursor.execute(query, tuple(heat_level_values))
        return fetchall_dicts(cursor)
    except Exception as exc:
        _log_db_error("get_peppers_by_heat_level_values", exc)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_distinct_scoville_levels():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT scoville_level
            FROM dbo.peppers
            WHERE scoville_level IS NOT NULL AND scoville_level <> ''
            ORDER BY scoville_level ASC
        """
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]
    except Exception as exc:
        _log_db_error("get_distinct_scoville_levels", exc)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# if the user want to see the information of a spicific pepper
def get_pepper_by_id(pepper_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT
                peppers.*,
                heat_levels.name AS heat_level_name,
                heat_levels.level_value AS heat_level_value,
                heat_levels.color AS heat_level_color,
                heat_levels.css_class AS heat_level_css_class,
                heat_levels.description AS heat_level_description
            FROM {PEPPERS_TABLE} AS peppers
            LEFT JOIN dbo.pepper_heat_levels AS heat_levels
                ON heat_levels.id = peppers.heat_level_id
            WHERE peppers.id = ?
        """, (pepper_id,))
        return fetchone_dict(cursor)
    except Exception as exc:
        _log_db_error("get_pepper_by_id", exc)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_peppers_by_heat_level_ids(heat_level_ids):
    return get_peppers_by_heat_level_values(heat_level_ids)


def update_pepper(pepper):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            UPDATE dbo.peppers
            SET
                name = ?,
                scientific_name = ?,
                origin_country = ?,
                color = ?,
                scoville_level = ?,
                heat_level_id = ?,
                heat_category = ?,
                description = ?,
                growing_tips = ?,
                image_url = ?,
                soil_type = ?,
                sunlight_needs = ?,
                temperature_range = ?,
                watering_needs = ?,
                irrigation_frequency = ?,
                water_amount = ?,
                season = ?,
                harvest_season = ?,
                days_to_harvest = ?,
                harvest_signs = ?,
                storage_tips = ?,
                warnings = ?
            WHERE id = ?
        """

        cursor.execute(query, (
            pepper.name,
            pepper.scientific_name,
            pepper.origin_country,
            pepper.color,
            pepper.scoville_level,
            pepper.heat_level_id,
            pepper.heat_category,
            pepper.description,
            pepper.growing_tips,
            pepper.image_url,
            pepper.soil_type,
            pepper.sunlight_needs,
            pepper.temperature_range,
            pepper.watering_needs,
            pepper.irrigation_frequency,
            pepper.water_amount,
            pepper.season,
            pepper.harvest_season,
            pepper.days_to_harvest,
            pepper.harvest_signs,
            pepper.storage_tips,
            pepper.warnings,
            pepper.id,
        ))

        conn.commit()
        return cursor.rowcount > 0

    except Exception as exc:
        _log_db_error("update_pepper", exc)
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_pepper_by_id(pepper_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.peppers WHERE id = ?", (pepper_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as exc:
        _log_db_error("delete_pepper_by_id", exc)
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_active_peppers_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM dbo.peppers")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count
