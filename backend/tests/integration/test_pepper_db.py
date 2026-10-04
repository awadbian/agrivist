import pytest

from backend.main import app
from backend.service import pepper_service


@pytest.fixture
def client():
    app.config["TESTING"] = True
    pepper_service.clear_pepper_cache()
    with app.test_client() as client:
        yield client
    pepper_service.clear_pepper_cache()


def test_list_peppers_without_filter(monkeypatch):
    pepper_service.clear_pepper_cache()
    fake_peppers = [
        {
            "id": 1,
            "name": "Red Chili",
            "color": "Red",
            "scoville_level": "30,000 - 50,000",
            "description": "Rich flavor with medium heat.",
            "image_url": "https://example.com/red.jpg",
            "scientific_name": "Capsicum annuum",
            "origin_country": "Mexico",
            "growing_tips": "Warm weather and steady watering.",
            "extra_info": "Often used in sauces.",
        }
    ]

    monkeypatch.setattr(pepper_service, "get_all_peppers", lambda: fake_peppers)
    monkeypatch.setattr(
        pepper_service,
        "get_peppers_by_scoville_level",
        lambda level: [],
    )

    peppers, selected_heat_level = pepper_service.list_peppers()

    assert peppers == fake_peppers
    assert selected_heat_level == []


def test_list_peppers_with_filter(monkeypatch):
    pepper_service.clear_pepper_cache()
    fake_peppers = [
        {
            "id": 2,
            "name": "Jalapeno",
            "color": "Green",
            "scoville_level": "2,500 - 8,000",
            "description": "Popular pepper with balanced heat.",
            "image_url": None,
            "scientific_name": "Capsicum annuum",
            "origin_country": "Mexico",
            "growing_tips": "Grow in full sun.",
            "extra_info": "Can be eaten fresh.",
        }
    ]

    monkeypatch.setattr(pepper_service, "get_all_peppers", lambda: [])
    monkeypatch.setattr(
        pepper_service,
        "get_peppers_by_scoville_level",
        lambda level: fake_peppers if level == "2,500 - 8,000" else [],
    )

    peppers, selected_heat_level = pepper_service.list_peppers("2,500 - 8,000")

    assert peppers == fake_peppers
    assert selected_heat_level == "2,500 - 8,000"


def test_pepper_varieties_page_displays_peppers(client, monkeypatch):
    fake_peppers = [
        {
            "id": 1,
            "name": "Red Chili",
            "color": "Red",
            "scoville_level": "30,000 - 50,000",
            "description": "Rich flavor with medium heat.",
            "image_url": "https://example.com/red.jpg",
            "scientific_name": "Capsicum annuum",
            "origin_country": "Mexico",
            "growing_tips": "Warm weather and steady watering.",
            "extra_info": "Often used in sauces.",
        },
        {
            "id": 2,
            "name": "Sweet Yellow Pepper",
            "color": "Yellow",
            "scoville_level": "0 - 500",
            "description": "Mild and fresh.",
            "image_url": "https://example.com/yellow.jpg",
            "scientific_name": "Capsicum annuum",
            "origin_country": "Israel",
            "growing_tips": "Needs full sun.",
            "extra_info": "Good for salads.",
        },
    ]

    monkeypatch.setattr("backend.main.list_peppers", lambda heat_level: (fake_peppers, ""))
    monkeypatch.setattr(
        "backend.main.list_heat_levels",
        lambda: ["0 - 500", "30,000 - 50,000"],
    )

    response = client.get("/pepper-varieties")
    response_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Red Chili" in response_text
    assert "Sweet Yellow Pepper" in response_text
    assert "Rich flavor with medium heat." in response_text
    assert "Mild and fresh." in response_text
    assert "Often used in sauces." in response_text


def test_pepper_varieties_page_filters_peppers(client, monkeypatch):
    filtered_peppers = [
        {
            "id": 3,
            "name": "Habanero",
            "color": "Orange",
            "scoville_level": "100,000 - 350,000",
            "description": "Very hot with fruity flavor.",
            "image_url": None,
            "scientific_name": "Capsicum chinense",
            "origin_country": "Caribbean",
            "growing_tips": "Needs warm temperatures.",
            "extra_info": "Known for fruity heat.",
        }
    ]

    monkeypatch.setattr(
        "backend.main.list_peppers",
        lambda heat_level: (filtered_peppers, heat_level),
    )
    monkeypatch.setattr(
        "backend.main.list_heat_levels",
        lambda: ["0 - 500", "100,000 - 350,000"],
    )

    response = client.get("/pepper-varieties?heat_level=100,000+-+350,000")
    response_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Habanero" in response_text
    assert "מוצגים 1 פלפלים עבור 1 רמות חריפות שנבחרו" in response_text


def test_pepper_varieties_page_empty_state(client, monkeypatch):
    monkeypatch.setattr("backend.main.list_peppers", lambda heat_level: ([], heat_level))
    monkeypatch.setattr("backend.main.list_heat_levels", lambda: [])

    response = client.get("/pepper-varieties?heat_level=0+-+500")
    response_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "אין זני פלפלים להצגה כרגע" in response_text


def test_pepper_varieties_admin_sees_add_button(client, monkeypatch):
    monkeypatch.setattr("backend.main.list_peppers", lambda heat_level: ([], ""))
    monkeypatch.setattr("backend.main.list_heat_levels", lambda: [])

    with client.session_transaction() as session:
        session["role"] = "admin"

    response = client.get("/pepper-varieties")
    response_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "הוסף פלפל חדש" in response_text


def test_add_pepper_redirects_non_admin(client):
    response = client.get("/admin/peppers/add", follow_redirects=False)

    assert response.status_code == 302
    assert "/pepper-varieties" in response.headers["Location"]
