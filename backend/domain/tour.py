class Tour:
    def __init__(
        self,
        title,
        price,
        duration_minutes,
        max_people,
        description,
        includes,
        image_url=None,
        available_from=None,
        available_until=None,
        is_active=True,
        tour_id=None,
    ):
        self.id = tour_id
        self.title = title
        self.price = price
        self.duration_minutes = duration_minutes
        self.max_people = max_people
        self.description = description
        self.includes = includes
        self.image_url = image_url
        self.available_from = available_from
        self.available_until = available_until
        self.is_active = is_active
