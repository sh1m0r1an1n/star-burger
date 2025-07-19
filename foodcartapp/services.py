from geopy.distance import geodesic
from geocoder_cache.services import get_coordinates_from_cache


def get_coordinates(address):
    """Получает координаты по адресу из кэша или API"""
    return get_coordinates_from_cache(address)


def get_restaurant_distances(delivery_address, restaurants):
    """Получает расстояния от адреса доставки до всех ресторанов"""
    distances = []
    delivery_coords = get_coordinates(delivery_address)
    
    if not delivery_coords:
        return []
    
    for restaurant in restaurants:
        if not restaurant.address:
            continue
            
        if restaurant.latitude and restaurant.longitude:
            try:
                restaurant_coords = (restaurant.latitude, restaurant.longitude)
                distance = geodesic(delivery_coords, restaurant_coords).kilometers
                distances.append((restaurant, round(distance, 2)))
            except ValueError:
                continue
        else:
            restaurant_coords = get_coordinates(restaurant.address)
            if restaurant_coords:
                try:
                    distance = geodesic(delivery_coords, restaurant_coords).kilometers
                    distances.append((restaurant, round(distance, 2)))
                except ValueError:
                    continue
    
    distances.sort(key=lambda x: x[1])
    return distances 