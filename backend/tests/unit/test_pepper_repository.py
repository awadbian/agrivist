from backend.data_access import pepper_repository
from backend.domain.pepper import Pepper


def test_create_pepper_stores_pepper_data_for_dynamic_display(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.executed_query = None
            self.executed_params = None
            self.lastrowid = 17
            self.closed = False

        def execute(self, query, params):
            self.executed_query = query
            self.executed_params = params

        def fetchone(self):
            return [17]

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self):
            self.cursor_instance = FakeCursor()
            self.committed = False
            self.closed = False

        def cursor(self):
            return self.cursor_instance

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    fake_connection = FakeConnection()
    monkeypatch.setattr(pepper_repository, "get_connection", lambda: fake_connection)

    pepper = Pepper(
        name="Jalapeno",
        color="Green",
        scoville_level="2,500 - 8,000",
        heat_category="Medium",
        description="Popular pepper with balanced heat.",
        scientific_name="Capsicum annuum",
        origin_country="Mexico",
        culinary_tips="Commonly used fresh or pickled.",
        growing_tips="Needs warm soil.",
        warnings="Wash hands after handling.",
        image_url="https://example.com/jalapeno.jpg",
        status="active",
        spray_info="No spray needed.",
        watering_needs="Moderate watering.",
        sunlight_needs="Full sun.",
        season="Spring / Summer.",
        use_cases="Sauces and pickles.",
        soil_type=None,
        temperature_range=None,
        irrigation_frequency=None,
        water_amount=None,
        harvest_season=None,
        days_to_harvest=None,
        harvest_signs=None,
        storage_tips=None,
        extra_info="Extra admin notes.",
    )

    pepper_id = pepper_repository.create_pepper(pepper)

    assert pepper_id == 17
    assert "INSERT INTO dbo.peppers" in fake_connection.cursor_instance.executed_query
    assert "OUTPUT INSERTED.id" in fake_connection.cursor_instance.executed_query

    assert fake_connection.cursor_instance.executed_params == (
        "Jalapeno",
        "Capsicum annuum",
        "Mexico",
        "Green",
        "2,500 - 8,000",
        None,
        "Medium",
        "Popular pepper with balanced heat.",
        "Commonly used fresh or pickled.",
        "Needs warm soil.",
        "Wash hands after handling.",
        "https://example.com/jalapeno.jpg",
        "active",
        "No spray needed.",
        "Moderate watering.",
        "Full sun.",
        "Spring / Summer.",
        "Sauces and pickles.",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "Extra admin notes.",
    )

    assert fake_connection.committed is True
    assert fake_connection.cursor_instance.closed is True
    assert fake_connection.closed is True