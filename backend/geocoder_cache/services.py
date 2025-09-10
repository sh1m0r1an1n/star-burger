import requests
from django.conf import settings
from .models import GeoPlace


def get_coordinates_batch(addresses):
    """Возвращает словарь {адрес: (lat, lng)}, берет координаты из БД или API Яндекса."""
    if not addresses:
        return {}
    
    if not settings.YANDEX_GEOCODER_API_KEY:
        return {}
    
    normalized_addresses = [' '.join(addr.split()) for addr in addresses if addr]
    
    existing_places = GeoPlace.objects.filter(address__in=normalized_addresses)
    coordinates = {}
    
    for place in existing_places:
        if place.latitude is not None and place.longitude is not None:
            coordinates[place.address] = (place.latitude, place.longitude)
    
    existing_addresses = {place.address for place in existing_places}
    missing_addresses = [addr for addr in normalized_addresses if addr not in existing_addresses]
    
    for address in missing_addresses:
        coords = _get_coordinates_from_api(address)
        
        GeoPlace.objects.update_or_create(
            address=address,
            defaults={
                'latitude': coords[0] if coords else None,
                'longitude': coords[1] if coords else None,
            }
        )
        
        if coords:
            coordinates[address] = coords
    
    return coordinates





def _get_coordinates_from_api(address):
    """Получает координаты по адресу из API Яндекса"""
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