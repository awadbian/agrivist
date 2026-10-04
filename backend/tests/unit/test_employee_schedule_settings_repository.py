from datetime import date

from backend.data_access import employee_schedule_settings_repository as repository


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


def test_get_closed_days_for_week_reads_only_closed_days(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.description = None
            self.calls = []
            self.closed = False

        def execute(self, query, params=None):
            self.calls.append((query, params))

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)
    monkeypatch.setattr(
        repository,
        "fetchall_dicts",
        lambda _cursor: [{
            "week_start_date": date(2026, 6, 14),
            "date": date(2026, 6, 19),
            "day_name": "friday",
            "is_closed": True,
        }],
    )

    closed_days = repository.get_closed_days_for_week(date(2026, 6, 14))

    assert closed_days == [{
        "week_start_date": date(2026, 6, 14),
        "date": date(2026, 6, 19),
        "day_name": "friday",
        "is_closed": True,
    }]
    assert len(cursor.calls) == 1
    assert "FROM dbo.employee_schedule_closed_days" in cursor.calls[0][0]
    assert "AND is_closed = 1" in cursor.calls[0][0]
    assert cursor.calls[0][1] == (date(2026, 6, 14),)
    assert cursor.closed is True
    assert connection.closed is True


def test_set_closed_day_updates_existing_day(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.rowcount = 1
            self.closed = False

        def execute(self, query, params=None):
            self.calls.append((query, params))

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.set_closed_day(
        date(2026, 6, 14),
        date(2026, 6, 19),
        "friday",
        True,
    )

    assert len(cursor.calls) == 1
    assert "UPDATE dbo.employee_schedule_closed_days" in cursor.calls[0][0]
    assert cursor.calls[0][1] == (
        date(2026, 6, 19),
        1,
        date(2026, 6, 14),
        "friday",
    )
    assert connection.committed is True
    assert cursor.closed is True
    assert connection.closed is True


def test_set_closed_day_inserts_missing_day(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.rowcount = 0
            self.closed = False

        def execute(self, query, params=None):
            self.calls.append((query, params))

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.set_closed_day(
        date(2026, 6, 14),
        date(2026, 6, 19),
        "friday",
        False,
    )

    assert len(cursor.calls) == 2
    assert "INSERT INTO dbo.employee_schedule_closed_days" in cursor.calls[1][0]
    assert cursor.calls[1][1] == (
        date(2026, 6, 14),
        date(2026, 6, 19),
        "friday",
        0,
    )
    assert connection.committed is True
    assert cursor.closed is True
    assert connection.closed is True
