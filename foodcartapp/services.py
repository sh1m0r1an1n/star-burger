import requests
from geopy.distance import geodesic
from django.conf import settings
from functools import lru_cache


@lru_cache(maxsize=1000)
def get_coordinates(address):
    """Получает координаты по адресу"""
    if not settings.YANDEX_GEOCODER_API_KEY:
        return None
        
    try:
        params = {
            'apikey': settings.YANDEX_GEOCODER_API_KEY,
            'format': 'json',
            'geocode': address,
            'lang': 'ru_RU'
        }
        
        response = requests.get(settings.YANDEX_GEOCODER_BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        feature_member = data['response']['GeoObjectCollection']['featureMember']
        
        if not feature_member:
            return None
            
        coords_str = feature_member[0]['GeoObject']['Point']['pos']
        longitude, latitude = map(float, coords_str.split())
        
        return latitude, longitude
        
    except (requests.RequestException, KeyError, ValueError):
        return None


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