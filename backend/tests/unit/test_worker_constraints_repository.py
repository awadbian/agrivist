from datetime import date, datetime
import inspect

from backend.data_access import worker_constraints_repository as repository


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


# Checks that saving constraints writes one submission row and six day rows.
def test_create_worker_constraints_uses_normalized_tables(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.closed = False

        def execute(self, query, params=None):
            self.calls.append((query, params))

        def fetchone(self):
            return [42]

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.create_worker_constraints(
        "worker@example.com",
        date(2026, 6, 7),
        {
            "sunday": "morning",
            "monday": "midday",
            "tuesday": "evening",
            "wednesday": "all_day",
            "thursday": "unavailable",
            "friday": "morning",
        },
        "note",
    )

    assert "INSERT INTO dbo.employee_constraint_submissions" in cursor.calls[0][0]
    assert "OUTPUT INSERTED.id" in cursor.calls[0][0]
    assert cursor.calls[0][1] == ("worker@example.com", date(2026, 6, 7), "note")

    day_insert_calls = [
        call for call in cursor.calls
        if "INSERT INTO dbo.employee_constraint_days" in call[0]
    ]
    assert len(day_insert_calls) == 6
    assert day_insert_calls[0][1] == (42, "sunday", "morning")
    assert day_insert_calls[-1][1] == (42, "friday", "morning")
    assert connection.committed is True
    assert connection.rolled_back is False
    assert cursor.closed is True
    assert connection.closed is True


# Checks that a failed day insert rolls back the whole save operation.
def test_create_worker_constraints_rolls_back_when_day_insert_fails(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.closed = False

        def execute(self, query, params=None):
            self.calls.append((query, params))
            if "INSERT INTO dbo.employee_constraint_days" in query:
                raise RuntimeError("duplicate day")

        def fetchone(self):
            return [42]

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    try:
        repository.create_worker_constraints(
            "worker@example.com",
            date(2026, 6, 7),
            {
                "sunday": "morning",
                "monday": "midday",
                "tuesday": "evening",
                "wednesday": "all_day",
                "thursday": "unavailable",
                "friday": "morning",
            },
            "note",
        )
    except RuntimeError as exc:
        assert str(exc) == "duplicate day"
    else:
        raise AssertionError("repository should re-raise database errors")

    assert connection.committed is False
    assert connection.rolled_back is True
    assert cursor.closed is True
    assert connection.closed is True


# Checks that normalized rows are rebuilt into the shape expected by the template.
def test_get_worker_constraints_returns_template_compatible_shape(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.description = None
            self.current_result = None
            self.closed = False

        def execute(self, query, params=None):
            if "FROM dbo.employee_constraint_submissions" in query:
                self.description = [
                    ("id",),
                    ("employee_email",),
                    ("week_start_date",),
                    ("notes",),
                    ("submitted_at",),
                ]
                self.current_result = [(
                    42,
                    "worker@example.com",
                    date(2026, 6, 7),
                    "note",
                    datetime(2026, 6, 1, 8, 30),
                )]
            elif "FROM dbo.employee_constraint_days" in query:
                self.description = [("day_of_week",), ("availability",)]
                self.current_result = [
                    ("sunday", "morning"),
                    ("monday", "midday"),
                    ("tuesday", "evening"),
                    ("wednesday", "all_day"),
                    ("thursday", "unavailable"),
                    ("friday", "morning"),
                ]

        def fetchone(self):
            if not self.current_result:
                return None
            return self.current_result[0]

        def fetchall(self):
            return self.current_result

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    submission = repository.get_worker_constraints("worker@example.com", date(2026, 6, 7))

    assert submission["id"] == 42
    assert submission["employee_email"] == "worker@example.com"
    assert submission["week_start_date"] == date(2026, 6, 7)
    assert submission["notes"] == "note"
    assert submission["sunday"] == "morning"
    assert submission["thursday"] == "unavailable"
    assert submission["friday"] == "morning"
    assert cursor.closed is True
    assert connection.closed is True


def test_save_worker_constraints_updates_existing_submission_without_duplicate(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.closed = False

        def execute(self, query, params=None):
            self.calls.append((query, params))

        def fetchone(self):
            return [42]

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    submission_id = repository.save_worker_constraints(
        "worker@example.com",
        date(2026, 6, 7),
        {
            "sunday": "evening",
            "monday": "all_day",
            "tuesday": "evening",
            "wednesday": "all_day",
            "thursday": "all_day",
            "friday": "morning",
        },
        "updated",
    )

    queries = "\n".join(query for query, _params in cursor.calls)
    assert submission_id == 42
    assert "SELECT id" in cursor.calls[0][0]
    assert "UPDATE dbo.employee_constraint_submissions" in queries
    assert "DELETE FROM dbo.employee_constraint_days" in queries
    assert "INSERT INTO dbo.employee_constraint_submissions" not in queries

    day_insert_calls = [
        call for call in cursor.calls
        if "INSERT INTO dbo.employee_constraint_days" in call[0]
    ]
    assert len(day_insert_calls) == 6
    assert day_insert_calls[0][1] == (42, "sunday", "evening")
    assert connection.committed is True
    assert connection.rolled_back is False
    assert cursor.closed is True
    assert connection.closed is True


# Checks that schema setup creates normalized tables and migrates legacy data.
def test_create_worker_constraints_table_creates_normalized_tables_and_migrates_legacy(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.closed = False

        def execute(self, query, params=None):
            self.calls.append((query, params))

        def fetchone(self):
            return [123]

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.create_worker_constraints_table()

    queries = "\n".join(query for query, _params in cursor.calls)
    assert "CREATE TABLE dbo.employee_constraint_submissions" in queries
    assert "UQ_employee_constraint_submissions_employee_week" in queries
    assert "CREATE TABLE dbo.employee_constraint_days" in queries
    assert "FK_employee_constraint_days_submissions" in queries
    assert "UQ_employee_constraint_days_submission_day" in queries
    assert "FROM dbo.employee_constraints AS legacy" in queries
    assert "FROM dbo.worker_constraint_submissions AS legacy" in queries
    assert connection.committed is True
    assert cursor.closed is True
    assert connection.closed is True


# Checks that worker constraints persistence does not use JSON or attendance files.
def test_worker_constraints_repository_does_not_use_json_storage():
    source = inspect.getsource(repository)

    assert "employee_attendance.json" not in source
    assert "ATTENDANCE_FILE" not in source
    assert "json.dump" not in source
    assert "json.load" not in source
