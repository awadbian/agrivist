from datetime import date

from backend.data_access import weekly_schedule_repository as repository


class FakeCursor:
    def __init__(self):
        self.description = None
        self.fetchone_result = None
        self.queries = []
        self.assignment_inserts = []
        self.rowcount = 0

    def execute(self, query, params=()):
        self.queries.append((query, params))
        self.rowcount = 0

        if "LOWER(assignments.employee_email) = LOWER(?)" in query:
            self.description = [
                ("week_start_date",),
                ("employee_email",),
                ("employee_name",),
                ("work_date",),
                ("day_name",),
                ("shift_type",),
                ("start_time",),
                ("end_time",),
                ("notes",),
            ]
            self.fetchone_result = None
        elif "SELECT id, COALESCE(schedule_status, status) AS status" in query:
            self.description = [("id",), ("status",)]
            self.fetchone_result = (12, "draft")
        elif "INSERT INTO dbo.weekly_schedule_assignments" in query:
            self.assignment_inserts.append(params)
        elif "DELETE FROM dbo.weekly_schedule_assignments" in query:
            self.rowcount = 0
        else:
            self.description = None
            self.fetchone_result = None

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def test_save_weekly_schedule_draft_replaces_existing_assignments(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.save_weekly_schedule_draft(
        date(2026, 6, 7),
        [
            {
                "employee_email": "worker@example.com",
                "employee_name": "Worker",
                "work_date": date(2026, 6, 7),
                "day_name": "sunday",
                "shift_type": "morning",
                "start_time": "07:00",
                "end_time": "14:00",
                "notes": None,
            }
        ],
    )

    delete_queries = [
        query for query, _params in cursor.queries
        if "DELETE FROM dbo.weekly_schedule_assignments" in query
    ]

    assert connection.committed is True
    assert len(delete_queries) == 1
    assert len(cursor.assignment_inserts) == 1
    assert cursor.assignment_inserts[0][0] == 12
    assert cursor.assignment_inserts[0][1] == "worker@example.com"
    assert cursor.assignment_inserts[0][5] == "morning"


def test_get_published_assignments_for_employee_filters_employee_and_published(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.get_published_assignments_for_employee(
        "worker@example.com",
        date(2026, 6, 7),
    )

    query, params = cursor.queries[0]

    assert "LOWER(assignments.employee_email) = LOWER(?)" in query
    assert "COALESCE(weeks.schedule_status, weeks.status) = 'published'" in query
    assert params == ("worker@example.com", date(2026, 6, 7))


def test_publish_weekly_schedule_marks_existing_week_published(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    schedule_id = repository.publish_weekly_schedule(date(2026, 6, 7))

    queries = [query for query, _params in cursor.queries]

    assert schedule_id == 12
    assert connection.committed is True
    assert any("SET status = 'published'" in query for query in queries)
    assert any("published_at = SYSUTCDATETIME()" in query for query in queries)


def test_delete_weekly_schedule_draft_deletes_assignments_and_week(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    deleted_count = repository.delete_weekly_schedule_draft(date(2026, 6, 7))

    queries = [query for query, _params in cursor.queries]

    assert deleted_count == 0
    assert connection.committed is True
    assert any("DELETE FROM dbo.weekly_schedule_assignments" in query for query in queries)
    assert any("SET status = 'draft'" in query for query in queries)


def test_delete_weekly_schedule_removes_published_week(monkeypatch):
    class PublishedCursor(FakeCursor):
        def execute(self, query, params=()):
            super().execute(query, params)
            if "SELECT id, COALESCE(schedule_status, status) AS status" in query:
                self.fetchone_result = (12, "published")

    cursor = PublishedCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.delete_weekly_schedule_draft(date(2026, 6, 7))

    queries = [query for query, _params in cursor.queries]

    assert connection.committed is True
    assert any("DELETE FROM dbo.weekly_schedule_assignments" in query for query in queries)
    assert any("SET status = 'draft'" in query for query in queries)
