import os
import json
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _read_appsettings_connection_string():
    appsettings_path = ROOT_DIR / "appsettings.json"
    if not appsettings_path.exists():
        return None

    with appsettings_path.open(encoding="utf-8") as appsettings_file:
        settings = json.load(appsettings_file)

    return settings.get("ConnectionStrings", {}).get("MyDbConnection")


def _resolve_sql_driver(pyodbc_module):
    configured_driver = os.getenv("AZURE_SQL_DRIVER")
    installed_drivers = pyodbc_module.drivers()

    if configured_driver:
        return configured_driver

    for driver_name in (
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server",
    ):
        if driver_name in installed_drivers:
            return driver_name

    raise ValueError("No SQL Server ODBC driver is installed on this machine")


def _ensure_odbc_driver(connection_string, driver):
    if "DRIVER=" in connection_string.upper():
        return connection_string

    return f"DRIVER={{{driver}}};{connection_string}"


def _normalize_ado_net_connection_string(connection_string):
    replacements = {
        "Initial Catalog=": "DATABASE=",
        "User ID=": "UID=",
        "Password=": "PWD=",
        "Encrypt=True": "Encrypt=yes",
        "Encrypt=False": "Encrypt=no",
        "TrustServerCertificate=True": "TrustServerCertificate=yes",
        "TrustServerCertificate=False": "TrustServerCertificate=no",
        "MultipleActiveResultSets=True": "MARS_Connection=yes",
        "MultipleActiveResultSets=False": "MARS_Connection=no",
    }

    normalized = connection_string
    for old_value, new_value in replacements.items():
        normalized = normalized.replace(old_value, new_value)

    return normalized


def get_connection():
    import pyodbc

    timeout = os.getenv("AZURE_SQL_TIMEOUT", "30")

    if not timeout.isdigit():
        raise ValueError("AZURE_SQL_TIMEOUT must be a number of seconds")

    connection_string = (
        os.getenv("AZURE_SQL_CONNECTION_STRING")
        or os.getenv("ConnectionStrings__MyDbConnection")
        or os.getenv("ConnectionStrings_MyDbConnection")
        or _read_appsettings_connection_string()
    )

    if connection_string:
        driver = _resolve_sql_driver(pyodbc)
        connection_string = _normalize_ado_net_connection_string(connection_string)
        connection_string = _ensure_odbc_driver(connection_string, driver)
        return pyodbc.connect(connection_string, timeout=int(timeout))

    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")
    driver = _resolve_sql_driver(pyodbc)

    missing = [
        name for name, value in {
            "AZURE_SQL_SERVER": server,
            "AZURE_SQL_DATABASE": database,
            "AZURE_SQL_USERNAME": username,
            "AZURE_SQL_PASSWORD": password,
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(f"Missing Azure SQL settings in .env: {', '.join(missing)}")

    connection_parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER=tcp:{server},1433",
        f"DATABASE={database}",
        f"UID={username}",
        f"PWD={password}",
        "Encrypt=yes",
        "TrustServerCertificate=no",
        f"Connection Timeout={timeout}",
    ]

    connection_string = ";".join(connection_parts) + ";"

    return pyodbc.connect(connection_string, timeout=int(timeout))


def fetchone_dict(cursor):
    row = cursor.fetchone()
    if row is None:
        return None

    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def fetchall_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
