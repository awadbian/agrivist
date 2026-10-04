from backend.data_access.tour_repository import (
    create_tour,
    delete_tour_by_id,
    get_active_tour_by_id,
    get_active_tours,
    get_all_tours,
    get_tour_by_id,
    update_tour,
)
from backend.domain.tour import Tour


def get_active_tour_packages():
    return get_active_tours()


def get_active_tour_package_by_id(package_id):
    return get_active_tour_by_id(package_id)


def get_tour_package_by_id(package_id):
    return get_tour_by_id(package_id)


def get_all_tour_packages():
    return get_all_tours()


def create_tour_package(title, price, duration_minutes, max_people, description, includes):
    tour = Tour(
        title=title,
        price=int(price),
        duration_minutes=int(duration_minutes),
        max_people=int(max_people),
        description=description,
        includes=includes,
    )
    return create_tour(tour)


def update_tour_package(package_id, title, price, duration_minutes, max_people, description, includes, is_active):
    tour = Tour(
        tour_id=package_id,
        title=title,
        price=int(price),
        duration_minutes=int(duration_minutes),
        max_people=int(max_people),
        description=description,
        includes=includes,
        is_active=bool(is_active),
    )
    return update_tour(tour)


def delete_tour_package(package_id):
    return delete_tour_by_id(package_id)
