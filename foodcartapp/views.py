import json
from django.templatetags.static import static
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from phonenumber_field.phonenumber import to_python

from .models import Product, Order, OrderItem
from .serializers import OrderSerializer, OrderReadSerializer


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
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    validated_data = serializer.validated_data
    
    with transaction.atomic():
        order = Order.objects.create(
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'], 
            phonenumber=validated_data['phonenumber'],
            address=validated_data['address']
        )
        
        for product_data in validated_data['products']:
            product = Product.objects.get(id=product_data['product'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=product_data['quantity']
            )
    
    order_serializer = OrderReadSerializer(order)
    return Response(order_serializer.data)
