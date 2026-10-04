import backend.main as main


def test_home_page_smoke_loads_without_database(monkeypatch):
    main.app.config["TESTING"] = True

    monkeypatch.setattr(
        main,
        "get_pending_tour_rating_for_user",
        lambda email: None
    )

    monkeypatch.setattr(
        main,
        "get_latest_tour_ratings",
        lambda limit=6: []
    )

    with main.app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200