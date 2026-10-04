from backend.service.pepper_service import empty_pepper_form_data, normalize_pepper_form


def test_normalize_pepper_form_keeps_known_fields_only():
    form_data = {
        "name": "Jalapeno",
        "scientific_name": "Capsicum annuum",
        "origin_country": "Mexico",
        "color": "Green",
        "scoville_level": "2,500 - 8,000",
        "heat_category": "Medium",
        "description": "Popular pepper.",
        "growing_tips": "Warm soil.",
        "image_url": "https://example.com/jalapeno.jpg",
        "unexpected_field": "ignored",
    }

    normalized = normalize_pepper_form(form_data)

    assert normalized["name"] == "Jalapeno"
    assert normalized["growing_tips"] == "Warm soil."
    assert "unexpected_field" not in normalized
    assert set(normalized) == set(empty_pepper_form_data())
