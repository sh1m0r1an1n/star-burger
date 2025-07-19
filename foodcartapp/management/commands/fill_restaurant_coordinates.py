from django.core.management.base import BaseCommand
from foodcartapp.models import Restaurant
from foodcartapp.services import get_coordinates


class Command(BaseCommand):
    help = 'Заполняет координаты ресторанов'

    def handle(self, *args, **options):
        restaurants = Restaurant.objects.filter(address__isnull=False).exclude(address='')
        
        for restaurant in restaurants:
            if not restaurant.latitude or not restaurant.longitude:
                coords = get_coordinates(restaurant.address)
                if coords:
                    restaurant.latitude, restaurant.longitude = coords
                    restaurant.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Координаты для {restaurant.name}: {coords}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Не удалось получить координаты для {restaurant.name}')
                    ) 