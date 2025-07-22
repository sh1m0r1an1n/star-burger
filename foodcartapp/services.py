from geopy.distance import geodesic


def distance_key(item):
    """Возвращает расстояние для сортировки, None заменяет на бесконечность."""
    distance = item[1]
    return float('inf') if distance is None else distance


def get_restaurant_distances(delivery_address, restaurants, restaurant_coords, order_coords):
    """Получает расстояния от адреса доставки до всех ресторанов, используя заранее подготовленные словари координат."""
    distances = []
    delivery_coords = order_coords.get(delivery_address)
    if not delivery_coords:
        return []
    for restaurant in restaurants:
        rest_coords = restaurant_coords.get(restaurant.address)
        if rest_coords and rest_coords[0] is not None and rest_coords[1] is not None:
            try:
                distance = geodesic(delivery_coords, rest_coords).kilometers
                distances.append((restaurant, round(distance, 2)))
            except ValueError:
                distances.append((restaurant, None))
        else:
            distances.append((restaurant, None))
    distances.sort(key=distance_key)
    return distances 