import json
from django.templatetags.static import static
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Order, OrderItem


@api_view(['GET'])
def banners_list_api(request):
    # FIXME move data to db?
    return Response([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ])


@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return Response(dumped_products)


@api_view(['POST'])
def register_order(request):
    order_data = request.data
    
    if 'products' not in order_data:
        return Response(
            {'products': 'Обязательное поле.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    products = order_data['products']
    
    if products is None:
        return Response(
            {'products': 'Это поле не может быть пустым.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not isinstance(products, list):
        return Response(
            {'products': f'Ожидался list со значениями, но был получен "{type(products).__name__}".'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(products) == 0:
        return Response(
            {'products': 'Этот список не может быть пустым.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    print(order_data)
    
    with transaction.atomic():
        order = Order.objects.create(
            firstname=order_data['firstname'],
            lastname=order_data['lastname'], 
            phonenumber=order_data['phonenumber'],
            address=order_data['address']
        )
        
        for product_data in products:
            product = get_object_or_404(Product, id=product_data['product'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=product_data['quantity']
            )
    
    return Response({'status': 'success'})
