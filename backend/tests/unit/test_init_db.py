from backend.data_access import init_db


class RecordingCursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))


def test_drop_users_role_default_constraint_uses_valid_dynamic_sql():
    cursor = RecordingCursor()

    init_db._drop_users_role_default_constraint(cursor)

    query = cursor.calls[0][0]
    assert "SET @sql = N'ALTER TABLE dbo.users DROP CONSTRAINT ' + QUOTENAME(@constraint_name)" in query
    assert "EXEC sp_executesql @sql" in query


def test_seed_roles_inserts_only_missing_roles():
    cursor = RecordingCursor()

    init_db._seed_roles(cursor)

    assert len(cursor.calls) == len(init_db.DEFAULT_ROLES)
    for (query, params), role_name in zip(cursor.calls, init_db.DEFAULT_ROLES):
        assert "IF NOT EXISTS" in query
        assert "INSERT INTO dbo.roles" in query
        assert params == (role_name, role_name)
