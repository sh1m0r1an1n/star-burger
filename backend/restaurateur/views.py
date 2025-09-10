from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order
from foodcartapp.services import get_restaurant_distances
from geocoder_cache.models import GeoPlace
from geocoder_cache.services import get_coordinates_batch


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.order_by('name'),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = (
        Order.objects
        .with_total_cost()
        .prefetch_related('items__product')
        .select_related('restaurant')
        .exclude(status='completed')
        .order_by('-created_at')
    )
    orders = orders.with_available_restaurants()

    all_restaurants = set()
    order_addresses = set()
    for order in orders:
        order_addresses.add(order.address)
        for restaurant in order.available_restaurants:
            all_restaurants.add(restaurant)
    restaurant_addresses = {r.address for r in all_restaurants if r.address}
    order_addresses = {a for a in order_addresses if a}

    all_addresses = list(restaurant_addresses) + list(order_addresses)
    all_coordinates = get_coordinates_batch(all_addresses)
    
    restaurant_coords = {addr: coords for addr, coords in all_coordinates.items() if addr in restaurant_addresses}
    order_coords = {addr: coords for addr, coords in all_coordinates.items() if addr in order_addresses}

    for order in orders:
        if order.available_restaurants:
            order.restaurant_distances = get_restaurant_distances(
                order.address,
                order.available_restaurants,
                restaurant_coords,
                order_coords
            )
        else:
            order.restaurant_distances = []

    return render(request, template_name='order_items.html', context={
        'order_items': orders,
    })
