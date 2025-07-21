from geopy.distance import geodesic
from geocoder_cache.models import GeoPlace
from geocoder_cache.services import get_coordinates_from_cache


def distance_key(item):
    """Возвращает расстояние для сортировки, None заменяет на бесконечность."""
    distance = item[1]
    return float('inf') if distance is None else distance


def get_restaurant_distances(delivery_address, restaurants):
    """Получает расстояния от адреса доставки до всех ресторанов"""
    distances = []
    restaurant_addresses = set(r.address for r in restaurants if r.address)
    cache_qs = GeoPlace.objects.filter(address__in=restaurant_addresses)
    cache_by_address = {obj.address: obj for obj in cache_qs}

    delivery_coords = get_coordinates_from_cache(delivery_address)
    if not delivery_coords:
        return []

    for restaurant in restaurants:
        if not restaurant.address:
            continue
        cache_obj = cache_by_address.get(restaurant.address)
        if cache_obj and cache_obj.latitude is not None and cache_obj.longitude is not None:
            try:
                restaurant_coords = (cache_obj.latitude, cache_obj.longitude)
                distance = geodesic(delivery_coords, restaurant_coords).kilometers
                distances.append((restaurant, round(distance, 2)))
            except ValueError:
                distances.append((restaurant, None))
        else:
            coords = get_coordinates_from_cache(restaurant.address)
            if coords:
                try:
                    distance = geodesic(delivery_coords, coords).kilometers
                    distances.append((restaurant, round(distance, 2)))
                except ValueError:
                    distances.append((restaurant, None))
            else:
                distances.append((restaurant, None))
    distances.sort(key=distance_key)
    return distances 