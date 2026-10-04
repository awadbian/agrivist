class Pepper:
    def __init__(
        self,
        name,
        color,
        scoville_level,
        description,
        image_url=None,
        pepper_id=None,
        scientific_name=None,
        origin_country=None,
        heat_category=None,
        heat_level_id=None,
        heat_level_name=None,
        heat_level_color=None,
        heat_level_css_class=None,
        heat_level_description=None,
        culinary_tips=None,
        growing_tips=None,
        warnings=None,
        status=None,
        spray_info=None,
        watering_needs=None,
        sunlight_needs=None,
        season=None,
        use_cases=None,
        soil_type=None,
        temperature_range=None,
        irrigation_frequency=None,
        water_amount=None,
        harvest_season=None,
        days_to_harvest=None,
        harvest_signs=None,
        storage_tips=None,
        extra_info=None,
    ):
        self.id = pepper_id
        self.name = name
        self.color = color
        self.scoville_level = scoville_level
        self.description = description
        self.image_url = image_url
        self.scientific_name = scientific_name
        self.origin_country = origin_country
        self.heat_category = heat_category
        self.heat_level_id = heat_level_id
        self.heat_level_name = heat_level_name
        self.heat_level_color = heat_level_color
        self.heat_level_css_class = heat_level_css_class
        self.heat_level_description = heat_level_description
        self.culinary_tips = culinary_tips
        self.growing_tips = growing_tips
        self.warnings = warnings
        self.status = status
        self.spray_info = spray_info
        self.watering_needs = watering_needs
        self.sunlight_needs = sunlight_needs
        self.season = season
        self.use_cases = use_cases
        self.soil_type = soil_type
        self.temperature_range = temperature_range
        self.irrigation_frequency = irrigation_frequency
        self.water_amount = water_amount
        self.harvest_season = harvest_season
        self.days_to_harvest = days_to_harvest
        self.harvest_signs = harvest_signs
        self.storage_tips = storage_tips
        self.extra_info = extra_info