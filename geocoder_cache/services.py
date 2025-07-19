import requests
from django.conf import settings
from .models import GeocoderCache


def get_coordinates_from_cache(address):
    """Получает координаты из кэша или API"""
    if not settings.YANDEX_GEOCODER_API_KEY:
        return None
    
    normalized_address = ' '.join(address.split())
    
    try:
        cached_result = GeocoderCache.objects.get(address=normalized_address)
        
        if cached_result.latitude is not None and cached_result.longitude is not None:
            return cached_result.latitude, cached_result.longitude
    except GeocoderCache.DoesNotExist:
        pass
    
    coords = _get_coordinates_from_api(normalized_address)
    
    GeocoderCache.objects.update_or_create(
        address=normalized_address,
        defaults={
            'latitude': coords[0] if coords else None,
            'longitude': coords[1] if coords else None,
        }
    )
    
    return coords


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