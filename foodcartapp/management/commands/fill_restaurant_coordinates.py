from django.core.management.base import BaseCommand
from foodcartapp.models import Restaurant
from geocoder_cache.services import get_coordinates_from_cache


class Command(BaseCommand):
    help = 'Заполняет координаты ресторанов'

    def handle(self, *args, **options):
        restaurants = Restaurant.objects.filter(address__isnull=False).exclude(address='')
        
        for restaurant in restaurants:
            if not restaurant.location:
                coords = get_coordinates_from_cache(restaurant.address)
                if coords:
                    from geocoder_cache.models import GeocoderCache
                    cache_obj, _ = GeocoderCache.objects.get_or_create(address=restaurant.address)
                    cache_obj.latitude, cache_obj.longitude = coords
                    cache_obj.save()
                    restaurant.location = cache_obj
                    restaurant.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Координаты для {restaurant.name}: {coords}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Не удалось получить координаты для {restaurant.name}')
                    ) 